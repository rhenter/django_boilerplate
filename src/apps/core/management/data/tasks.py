import pytz

periodic_tasks_data = [
    {
        'name': 'recover_delivery_danfes',
        'task': 'apps.invoice.tasks.recover_delivery_danfes',
        'interval_id': {'every': 5, 'period': 'minutes'},
        'args': [], 'kwargs': {},
    },
    {
        'name': 'process_account_legal_lifecycle',
        'task': 'apps.accounts.tasks.process_account_legal_lifecycle',
        'interval_id': {'every': 15, 'period': 'minutes'},
        'args': [], 'kwargs': {},
    },
    {
        'name': 'recover_fiscal_invoices',
        'task': 'apps.financial.tasks.recover_fiscal_invoices',
        'interval_id': {'every': 15, 'period': 'minutes'},
        'args': [], 'kwargs': {},
    },
    {
        'name': 'recover_commercial_emails',
        'task': 'apps.notification.tasks.recover_commercial_emails',
        'interval_id': {'every': 5, 'period': 'minutes'},
        'args': [], 'kwargs': {},
    },
    {
        'name': 'recover_contract_changes',
        'task': 'apps.financial.tasks.recover_contract_changes',
        'interval_id': {'every': 5, 'period': 'minutes'},
        'args': [], 'kwargs': {},
    },
    {
        'name': 'expire_account_trials',
        'task': 'apps.accounts.tasks.expire_account_trials',
        'crontab_id': {
            'minute': '0',
            'hour': '*',
            'day_of_week': '*',
            'day_of_month': '*',
            'month_of_year': '*',
            'timezone': pytz.timezone("UTC")
        },
        'args': [],
        'kwargs': {}
    },
    {
        'name': 'reconcile_payment_subscriptions',
        'task': 'apps.financial.tasks.reconcile_payment_subscriptions',
        'interval_id': {
            'every': 15,
            'period': 'minutes'
        },
        'args': [],
        'kwargs': {}
    },
    {
        'name': 'refresh_account_usage',
        'task': 'apps.accounts.tasks.refresh_account_usage',
        'interval_id': {
            'every': 1,
            'period': 'hours'
        },
        'args': [],
        'kwargs': {}
    },
]
