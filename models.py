from . import db

# --- CONFIGURABLE TABLE NAMES ---
# You can easily change the table names here in the future.
TABLE_CONFIG = {
    'ancient': {
        'keys': 'dynasty_keys_test_v1',
        'data': 'coin_data_test_v3'
    },
    'medieval': {
        'keys': 'medieval_dynasty_keys',
        'data': 'coin_data_test_v4'
    },
    'modern': {
        'keys': 'modern_dynasty_keys',
        'data': 'coin_data_test_v5'
    }
}


# --- MIXIN CLASSES (to avoid repeating code) ---
# This defines the common structure for all your key tables.
class DynastyKeyMixin:
    id = db.Column(db.Integer, primary_key=True)
    dynasty = db.Column(db.String(255))
    king_name = db.Column(db.String(255))
    code = db.Column(db.String(10), unique=True)


# This defines the common structure for all your coin data tables.
class CoinDataMixin:
    # Mapped to the uppercase column names in your MySQL database.
    s_no = db.Column('SNO', db.Integer, primary_key=True)
    code = db.Column('CODE', db.String(10), unique=True)
    details = db.Column('DETAILS', db.Text)

    def to_dict_with_key_info(self, key_info):
        """Helper function to combine coin data with dynasty/king info."""
        return {
            's_no': self.s_no,
            'code': self.code,
            'details': self.details,
            'dynasty': key_info.dynasty if key_info else 'N/A',
            'king_name': key_info.king_name if key_info else 'N/A',
        }


# --- ANCIENT INDIA TABLE MODELS ---
class AncientDynastyKey(db.Model, DynastyKeyMixin):
    __tablename__ = TABLE_CONFIG['ancient']['keys']


class AncientCoinData(db.Model, CoinDataMixin):
    __tablename__ = TABLE_CONFIG['ancient']['data']


# --- MEDIEVAL INDIA TABLE MODELS ---
class MedievalDynastyKey(db.Model, DynastyKeyMixin):
    __tablename__ = TABLE_CONFIG['medieval']['keys']


class MedievalCoinData(db.Model, CoinDataMixin):
    __tablename__ = TABLE_CONFIG['medieval']['data']


# --- MODERN INDIA TABLE MODELS ---
class ModernDynastyKey(db.Model, DynastyKeyMixin):
    __tablename__ = TABLE_CONFIG['modern']['keys']


class ModernCoinData(db.Model, CoinDataMixin):
    __tablename__ = TABLE_CONFIG['modern']['data']

