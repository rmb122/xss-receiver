import request from "./Request";

class UploadFile {
    async get_files() {
        return (await request.get('/upload_file/list')).payload;
    }

    async upload_file(file) {
        let form = new FormData();
        form.append('file', file);
        return await request.post('/upload_file/add', form);
    }

    async preview_file(filename) {
        return await request.post('/upload_file/preview', {'filename': filename});
    }

    async modify_file(filename, new_filename, content) {
        return await request.post('/upload_file/modify', {
            'filename': filename,
            'new_filename': new_filename,
            'content': content
        });
    }

    async delete_file(filename) {
        return await request.post('/upload_file/delete', {'filename': filename});
    }

    async add_directory(directory_name) {
        return await request.post('/upload_file/add_directory', {'directory_name': directory_name})
    }

    async delete_directory(directory_name) {
        return await request.post('/upload_file/delete_directory', {'directory_name': directory_name})
    }

    async modify_directory(directory_name, new_directory_name) {
        return await request.post('/upload_file/modify_directory', {'directory_name': directory_name, 'new_directory_name': new_directory_name})
    }
}

let upload_file = new UploadFile();
export default upload_file;