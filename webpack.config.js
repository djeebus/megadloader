const webpack = require('webpack')
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = env => {
    return {
        entry: './frontend/index.js',
        module: {
            rules: [
                {
                    test: /\.(jsx?)$/,
                    exclude: /node_modules/,
                    use: ['babel-loader']
                }
            ]
        },
        resolve: {
            extensions: ['*', '.js', '.jsx']
        },
        plugins: [
            new HtmlWebpackPlugin({
                template: 'frontend/index.html',
                inject: 'body',
            }),
            new webpack.DefinePlugin({
                'process.env.API_ROOT': JSON.stringify(env.API_ROOT),
            }),
        ],
    }
}
