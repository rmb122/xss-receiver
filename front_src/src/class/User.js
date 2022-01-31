import request from "./Request";
import utils from "@/class/Utils";

class User {
    _is_login = false;

    async is_login() {
        if (this._is_login === true) {
            return true;
        } else {
            if (request.load_jwt()) {
                let data = await request.get('/auth/status');
                if (data.code === request.CODE_SUCCESS) {
                    this._is_login = true;
                    return true;
                } else {
                    this.logout();
                    return false;
                }
            } else {
                return false;
            }
        }
    }

    async login(username, password) {
        password = utils.pbkdf2(password, username);

        let data = await request.post('/auth/login', {'username': username, 'password': password});
        if (data.code === request.CODE_SUCCESS) {
            request.set_jwt(data.payload.token);
            utils.save_localstorage(utils.localstorage_keys.CURRENT_USERNAME, username);
            utils.save_localstorage(utils.localstorage_keys.CURRENT_USERTYPE, data.payload.user_type);
            this._is_login = true;
            return true;
        } else {
            return false;
        }
    }

    get_jwt() {
        return window.localStorage.getItem(utils.localstorage_keys.AUTHORIZATION);
    }

    is_admin() {
        return utils.load_localstorage(utils.localstorage_keys.CURRENT_USERTYPE) === utils.user_type.USER_TYPE_ADMIN;
    }

    logout() {
        this._is_login = false;
        localStorage.removeItem('Authorization');
    }

    async change_password(original_password, new_password) {
        return await request.post('/auth/change_password', {'original_password': original_password, 'new_password': new_password});
    }

    async change_other_user_password(target_user, password) {
        return await request.post('/auth/change_password', {'target_user': target_user, 'new_password': password});
    }

    async register_user(username, password) {
        return await request.post('/auth/register', {'username': username, 'password': password});
    }

    async list_user() {
        return await request.get('/auth/list_user');
    }

    async delete_user(username) {
        return await request.post('/auth/delete', {'username': username});
    }
}

let user = new User();
export default user;