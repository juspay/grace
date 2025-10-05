const path = require('path');
const webpack = require('webpack');

module.exports = {
  entry: './dist/index.js',
  target: 'node',
  mode: 'production',
  output: {
    path: path.resolve(__dirname, 'bundle'),
    filename: 'mass-cli.js',
    clean: true
  },
  optimization: {
    minimize: true,
    usedExports: true,
    sideEffects: false
  },
  resolve: {
    extensions: ['.js', '.json'],
    alias: {
      // Resolve native modules
      'blessed': path.resolve(__dirname, 'node_modules/blessed'),
      'chalk': path.resolve(__dirname, 'node_modules/chalk')
    }
  },
  externals: {
    // Keep these as external to reduce bundle size
    'playwright': 'commonjs playwright',
    'sharp': 'commonjs sharp',
    // Exclude problematic blessed dependencies
    'term.js': 'commonjs term.js',
    'pty.js': 'commonjs pty.js'
  },
  plugins: [
    new webpack.BannerPlugin({
      banner: '#!/usr/bin/env node\n\n// MASS CLI Deep Research Tool - Bundled Version\n// Inspired by Claude Code architecture\n',
      raw: true
    }),
    new webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify('production'),
      'process.env.CLI_VERSION': JSON.stringify('2.0.0')
    })
  ],
  module: {
    rules: [
      {
        test: /\.node$/,
        use: 'node-loader'
      }
    ]
  },
  stats: {
    warnings: false
  }
};