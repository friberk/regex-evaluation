
import { parse } from '@babel/parser';
import * as fs from 'fs/promises';
import traverse from "@babel/traverse";
import * as types from '@babel/types';
import * as net from "net";
import * as rl from 'readline';
import * as async from 'async';
import cluster from 'cluster';

interface RegexObject {
    sourceFile: string;
    pattern: string;
    lineNo: number;
    flags: string;
}

export interface RegexObjectSerialized {
    source_file: string;
    pattern: string;
    line_no: number;
    flags: string;
}

export const serializeRegexObject = (regexObj: RegexObject): RegexObjectSerialized => ({
    source_file: regexObj.sourceFile,
    pattern: regexObj.pattern,
    flags: regexObj.flags,
    line_no: regexObj.lineNo,
});

export async function parseFile(filePath: string): Promise<RegexObject[]> {

    const fileContentsBuffer = await fs.readFile(filePath);
    const fileContents = fileContentsBuffer.toString()

    let ast = parse(fileContents, {
        plugins: ['typescript', 'decorators-legacy'],
        sourceFilename: filePath,
        sourceType: 'module'
    });

    if (!ast) {
        ast = parse(fileContents, {
            plugins: ['typescript', 'decorators-legacy'],
            sourceFilename: filePath,
            sourceType: 'script'
        });
    }

    // Still can't parse the AST
    if (!ast) {
        return [];
    }

    const regexObjs: RegexObject[] = [];

    traverse(ast, {
        RegExpLiteral(path) {
            regexObjs.push({
                pattern: path.node.pattern,
                flags: path.node.flags,
                sourceFile: filePath,
                lineNo: path.node.loc.start.line,
            });
        },
        NewExpression(path) {
            const node = path.node;
            if (path.node.callee.type === 'Identifier' && path.node.callee.name === 'RegExp') {
                const pattern = (node['arguments'][0].type === 'StringLiteral') ?
                    node['arguments'][0].value : 'DYNAMIC-PATTERN';

                let flags = '';
                if (2 <= node['arguments'].length) {
                    flags = (node['arguments'][1].type === 'StringLiteral') ?
                        node['arguments'][1].value : 'DYNAMIC-FLAGS';
                }

                regexObjs.push({
                    pattern: pattern,
                    flags: flags,
                    sourceFile: filePath,
                    lineNo: path.node.loc.start.line,
                });
            }
        },
        // The argument to the search, match, and matchAll String.prototype
        // methods is implicitly converted to a RegExp.
        CallExpression(path) {
            const methods = ['search', 'match', 'matchAll'];
            const callee = path.node.callee;
            if (path.node.arguments.length === 1
                && types.isMemberExpression(callee)
                && types.isIdentifier(callee.property)
                && methods.includes(callee.property.name)) {

                const arg = path.node.arguments[0];
                const pattern = arg.type === 'StringLiteral' ? arg.value : 'DYNAMIC-PATTERN';
                regexObjs.push({
                    pattern: pattern,
                    flags: '',
                    sourceFile: filePath,
                    lineNo: path.node.loc.start.line,
                });
            }
        }
    });

    return regexObjs;
}

// start main
if (process.argv.length < 3) {
    console.error(`usage: ${process.argv[1]} <listeningPath> [concurrency]`)
}

const listenPath = process.argv[2];

const server = net.createServer({}, connection => {

    console.log(`Client connected on process ${cluster.worker?.id}`);
    connection.on('close', () => {
        console.log(`client disconnected from ${cluster.worker?.id}`);
    })

    const reader = rl.createInterface(connection);
    const parserQueue = async.queue((task: string | null, callback) => {
        if (task !== null) {
            parseFile(task)
                .then(results => {
                    console.log(`Got ${results.length} results`);
                    const serializedObjs = results.map(obj => serializeRegexObject(obj))
                    connection.write(JSON.stringify(serializedObjs))
                    connection.write('\r\n')
                    callback()
                })
                .catch(err => {
                    console.error(`Error while parsing ${task}: ${err}`)
                    callback(err);
                })
        } else {
            // we reached the end of the connection
            console.log('null task received. Closing connection...');
            connection.end()
            callback()
        }
    });

    reader.on('line', line => {
        console.log(`Got line: ${line}`);
        const path = line.trim();
        if (path.length > 0) {
            console.log(`Parsing path: ${path}`)
            parserQueue.push(path)
        } else {
            console.log('Reached end of packages');
            reader.close();
            parserQueue.push(null)
        }
    });

    connection.on('error', err => {
        throw err
    });

    connection.on('close', () => {
        console.log('Connection closed');
    })
});
server.listen(listenPath)

process.on('SIGINT', () => {
    console.log(`Server on ${process.pid} terminated`);
    server.close()
});

console.log(`Accepting connections at ${listenPath}...`);
