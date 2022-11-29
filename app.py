from xss_receiver import app, system_config

if __name__ == "__main__":
    if not system_config.APP_DEBUG:
        app.run(host='0.0.0.0', port=80, fast=True, access_log=False, debug=False)
    else:
        from sanic_cors import CORS

        CORS(app)
        app.run(host='127.0.0.1', port=5000, fast=False, access_log=True, debug=True)
