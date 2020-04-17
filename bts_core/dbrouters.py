class AssetDbRouter:
    """
    A router to control all database operations on models in the
    auth and contenttypes applications.
    """

    def db_for_read(self, model, **hints):
        """
        Attempts to read asset_db models go to asset_db_pat.
        """
        if model._meta.app_label == 'bts_asset_db':
            return 'pat'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Attempts to write asset_db models go to asset_db_pat.
        """
        if model._meta.app_label == 'bts_asset_db':
            return 'pat'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Resort to default relational behaviour
        """
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure asset_db apps only appear in the
        'asset_db_pat' database.
        """
        if app_label == 'bts_asset_db':
            return db == 'pat'
        else:
            return db != 'pat'
