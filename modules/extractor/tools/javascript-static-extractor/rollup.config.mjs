
import { nodeResolve } from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import json from '@rollup/plugin-json';

export default {
    plugins: [nodeResolve(), commonjs(), json()],
    input: 'build/main.js',
    output: {
        file: 'bin/js-static-extractor.js',
        format: 'cjs'
    }
};
