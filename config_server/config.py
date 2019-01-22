from config_server.utils import dict_merge


class Config(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self["base"] = None

    def __getitem__(self, item):
        if item not in self:
            raise KeyError
        if dict.__getitem__(self, "base"):
            if dict.__getitem__(self, item) is not None:
                return dict_merge(
                    dict.__getitem__(self, "base"),
                    dict.__getitem__(self, item)
                )
            else:
                return dict.__getitem__(self, "base")
        return dict.__getitem__(self, item)

    def update_base(self, content):
        self["base"] = content

    def __repr__(self):
        return f"<Config: {dict.__repr__(self)}"
