// vue.config.js
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = {
    productionSourceMap: false,
    publicPath: "./",
    lintOnSave: false,
    configureWebpack: {
        plugins: [
            new BundleAnalyzerPlugin()
        ],
        externals: {
            'vue': 'Vue',
            'element-ui': 'ElementUI',
        }
    }
};