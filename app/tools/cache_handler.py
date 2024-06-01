from flask_caching import Cache

cache : Cache = Cache()

def init_cache(app):
    global cache
    cache.init_app(app)
