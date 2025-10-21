import pymysql
import yaml
from pathlib import Path

class baseObject:
    def setup(self):
        # initialize storage for this object
        self.data = []
        self.errors = []
        self.fields = []
        self.pk = None

        # load configuration from config.yml located beside this file
        cfg_path = Path(__file__).parent / "config.yml"
        raw = cfg_path.read_text()
        config = yaml.safe_load(raw)

        # table name mapping for this class
        self.tn = config['tables'][type(self).__name__]

        # establish DB connection
        db_cfg = config['db']
        self.conn = pymysql.connect(
            host=db_cfg['host'],
            port=db_cfg['port'],
            user=db_cfg['user'],
            passwd=db_cfg['pw'],
            db=db_cfg['db'],
            autocommit=True
        )
        self.cur = self.conn.cursor(pymysql.cursors.DictCursor)

        # load column metadata
        self.getFields()

    def getFields(self):
        self.fields = []
        sql = f"DESCRIBE `{self.tn}`;"
        self.cur.execute(sql)
        for row in self.cur:
            if row['Extra'] == 'auto_increment':
                self.pk = row['Field']
            elif row['Field'] == 'created_at':
                continue
            else:
                self.fields.append(row['Field'])

    def set(self, d):
        self.data.append(d)

    def insert(self, n=0):
        cols = ', '.join(f"`{field}`" for field in self.fields)
        vals_placeholders = ', '.join('%s' for _ in self.fields)
        sql = f"INSERT INTO `{self.tn}` ({cols}) VALUES ({vals_placeholders});"
        tokens = [self.data[n][f] for f in self.fields]
        self.cur.execute(sql, tokens)
        self.data[n][self.pk] = self.cur.lastrowid
        return True

    def update(self, n=0):
        set_clauses = ', '.join(f"`{field}` = %s" for field in self.fields if field in self.data[n])
        sql = f"UPDATE `{self.tn}` SET {set_clauses} WHERE `{self.pk}` = %s;"
        params = [self.data[n][field] for field in self.fields if field in self.data[n]]
        params.append(self.data[n][self.pk])
        self.cur.execute(sql, params)

    def getAll(self):
        sql = f"SELECT * FROM `{self.tn}`;"
        self.cur.execute(sql)
        self.data = list(self.cur.fetchall())

    def getById(self, id):
        sql = f"SELECT * FROM `{self.tn}` WHERE `{self.pk}` = %s;"
        self.cur.execute(sql, [id])
        self.data = list(self.cur.fetchall())

    def getByField(self, field, value):
        sql = f"SELECT * FROM `{self.tn}` WHERE `{field}` = %s;"
        self.cur.execute(sql, [value])
        self.data = list(self.cur.fetchall())

    def deleteById(self, id):
        sql = f"DELETE FROM `{self.tn}` WHERE `{self.pk}` = %s;"
        self.cur.execute(sql, [id])
        self.data = []

    def createBlank(self):
        blank = {field: '' for field in self.fields}
        self.set(blank)
