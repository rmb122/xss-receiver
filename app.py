from xss_receiver import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, fast=True, access_log=False, debug=False)
