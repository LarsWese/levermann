class ShareNotExist(Exception):
    def __init__(self, isin: str):
        self.isin = isin
        Exception.__init__(self, f'Share "{isin}" does not exist ')
