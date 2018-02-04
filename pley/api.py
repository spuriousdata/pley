import requests


class Plex(object):
    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.__filter = None
        self.reset()

    def reset(self):
        self.__history = ["/library/sections"]
        self.__cache = {}
        self.__session = requests.Session()

    def filter(self, **kwargs):
        self.__filter = kwargs

    @property
    def headers(self):
        return {
            'X-Plex-Token': self.token,
            'X-Plex-Provides': 'player,controller',
            'Accept': 'application/json',
        }

    def get_abs_key(self, key):
        if key.startswith('/'):
            return key
        else:
            return self.__history[-1] + "/" + key

    def down(self, key):
        self.__history.append(self.get_abs_key(key))
        return self.get()

    def stream(self, key):
        return self.__session.get(self.host + self.get_abs_key(key),
                                  headers=self.headers, stream=True)

    def up(self):
        if self.__history:
            self.__history = self.__history[:-1]
        return self.get()

    def get(self):
        if self.path not in self.__cache:
            data = self.get_items(self.__request())
            if self.__filter and len(self.__history) == 1:
                data = [x for x in data if self.filter_item(x)]
            self.__cache[self.path] = data
        return self.__cache[self.path]

    def getkey(self, idx):
        return self.__cache[self.path][idx]['key']

    def filter_item(self, item):
        for k, v in self.__filter.items():
            if item[k] != v:
                return False
        return True

    def get_items(self, d):
        if 'MediaContainer' in d:
            d = d['MediaContainer']
        if 'Directory' in d:
            d = d['Directory']
        if 'Metadata' in d:
            d = d['Metadata']
        return d

    def __request(self):
        resp = self.__session.get(self.url, headers=self.headers)
        return resp.json()

    @property
    def path(self):
        return self.__history[-1]

    @property
    def url(self):
        return self.host + self.path


if __name__ == '__main__':
    import sys
    p = Plex(sys.argv[1], sys.argv[2])
    import pudb
    pudb.set_trace()
    p.filter(type='artist')
    p.get()
    p.down('19')
    p.down('all')
