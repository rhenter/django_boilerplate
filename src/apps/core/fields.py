import gzip
import io
import json

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, Point
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.text import compress_string
from rest_framework import serializers, ISO_8601


class CustomDateTimeField(serializers.DateTimeField):

    def to_representation(self, value):
        if not value:
            return None

        output_format = getattr(self, 'format', settings.DATETIME_FORMAT)

        if output_format is None or isinstance(value, str):
            return value

        value = self.enforce_timezone(value)

        if output_format.lower() == ISO_8601:
            value = value.isoformat()
            return value
        return value.strftime(output_format)


class PointJSONField(serializers.Field):
    def to_representation(self, value):
        if not value:
            return None
        try:
            # value is a GEOS Point: x=longitude, y=latitude
            return {"longitude": value.x, "latitude": value.y}
        except Exception:
            return None

    def to_internal_value(self, data):
        if data in (None, "", {}):
            return None
        # Accept GeoJSON object, [lng, lat] array, JSON-encoded strings, comma strings, or WKT
        try:
            # 1) Python list/tuple
            if isinstance(data, (list, tuple)) and len(data) == 2:
                lng, lat = float(data[0]), float(data[1])
                return Point(lng, lat, srid=4326)

            # 2) Dict: GeoJSON or lat/lng keys
            if isinstance(data, dict):
                # GeoJSON
                coords = data.get("coordinates")
                if data.get("type") == "Point" and isinstance(coords, (list, tuple)) and len(coords) == 2:
                    lng, lat = float(coords[0]), float(coords[1])
                    return Point(lng, lat, srid=4326)
                # {lng: ..., lat: ...} or {longitude: ..., latitude: ...}
                if {"lng", "lat"}.issubset(data.keys()):
                    return Point(float(data["lng"]), float(data["lat"]), srid=4326)
                if {"longitude", "latitude"}.issubset(data.keys()):
                    return Point(float(data["longitude"]), float(data["latitude"]), srid=4326)

            # 3) Strings
            if isinstance(data, str):
                s = data.strip()
                # JSON-encoded array/dict coming from multipart forms
                if s.startswith("[") or s.startswith("{"):
                    try:
                        parsed = json.loads(s)
                        return self.to_internal_value(parsed)
                    except Exception:
                        # fall through to other parsers
                        pass
                # Comma-separated "lng,lat"
                if "," in s:
                    parts = [p.strip() for p in s.split(",")]
                    if len(parts) == 2:
                        lng, lat = float(parts[0]), float(parts[1])
                        return Point(lng, lat, srid=4326)
                # Try WKT/GeoJSON via GEOS
                geom = GEOSGeometry(s, srid=4326)
                if geom.geom_type == "Point":
                    return geom
        except Exception:
            # Normalize any parsing error into a validation error below
            pass
        raise serializers.ValidationError("Invalid location. Use GeoJSON Point, [lng, lat], 'lng,lat' or JSON string.")


class CompressedBinaryField(models.BinaryField):
    compress = compress_string

    @staticmethod
    def uncompress(s):
        zbuf = io.BytesIO(s)
        zfile = gzip.GzipFile(fileobj=zbuf)
        ret = zfile.read()
        zfile.close()
        return ret

    def get_db_prep_save(self, value, connection=None, prepared=False):
        if value is not None and prepared is False:
            value = CompressedBinaryField.compress(value)
        return models.BinaryField.get_db_prep_save(self, value, connection)

    def is_binary(self, value):
        return value and (type(value) == bytes or isinstance(value, memoryview))

    def _get_val_from_obj(self, obj):
        val = obj and getattr(obj, self.attname)
        if self.is_binary(val):
            return CompressedBinaryField.uncompress(val)
        if val is None:
            return self.get_default()
        return val

    def post_init(self, instance=None, **kwargs):
        value = self._get_val_from_obj(instance)
        setattr(instance, self.attname, value)

    def contribute_to_class(self, cls, name, private_only=False):
        super(CompressedBinaryField, self).contribute_to_class(cls, name)
        models.signals.post_init.connect(self.post_init, sender=cls)

    def get_internal_type(self):
        return 'BinaryField'


class CompressedJSONField(CompressedBinaryField):
    encoder = DjangoJSONEncoder

    def __init__(self, *args, **kwargs):
        self.encoder = kwargs.pop('encoder', DjangoJSONEncoder)
        super().__init__(*args, **kwargs)

    def get_db_prep_save(self, value, connection=None, prepared=False):
        if value is not None and prepared is False:
            value = json.dumps(value, cls=self.encoder).encode('utf-8')
        return super().get_db_prep_save(value, connection, prepared)

    def _get_val_from_obj(self, obj):
        if obj:
            val = super()._get_val_from_obj(obj)
            if self.is_binary(val):
                return json.loads(val.decode('utf-8'))
            return val
        else:
            return self.get_default()
