
if (RegExp.prototype.__monkey_patched === undefined) {
  const outputUsageRecord = (record) => {
    const output = process.env['DYN_EXTRACTOR_OUTPUT_PATH']
    if (output) {

      try {
        const recordPayload = JSON.stringify(record, (key, value) => {
          if (key !== 'subject' || typeof value == 'string') {
            return value;
          }

          return value?.toString() ?? 'null'
        });

        import('fs')
            .then(monkeyFs => monkeyFs.appendFileSync(output, recordPayload + '\n'))
            .catch(err => { throw err })
      } catch (err) {
        console.error(err)
      }
    }
  }

  const generateStack = () => {
    const genStackValue = process.env['DYN_EXTRACTOR_REPORT_STACKTRACE']
    if (genStackValue?.toLowerCase?.() === 'true') {
      return new Error().stack;
    } else {
      return ''
    }
  }

  RegExp.prototype.__monkey_patched = true;

  RegExp.prototype.disableMonkeyPatch = function () {
    const monkeyPatchedExec = RegExp.prototype.exec;
    RegExp.prototype.exec = RegExp.prototype.innerExec;
    const monkeyPatchedTest = RegExp.prototype.test;
    RegExp.prototype.test = RegExp.prototype.innerTest;

    return [monkeyPatchedExec, monkeyPatchedTest];
  }

  RegExp.prototype.enableMonkeyPatch = function (execMonkey, testMonkey) {
    RegExp.prototype.exec = execMonkey;
    RegExp.prototype.test = testMonkey;
  }

  RegExp.prototype.innerTest = RegExp.prototype.test;
  RegExp.prototype.test = function (subject) {
    const stack = generateStack()
    const useRecord = {
      pattern: this.source,
      subject,
      stack,
      funcName: 'RegExp#test',
      def: false
    };
    outputUsageRecord(useRecord);
    const result = this.innerTest(subject);
    return result;
  }

  RegExp.prototype.innerExec = RegExp.prototype.exec;
  RegExp.prototype.exec = function (subject) {
    // const [exec, test] = this.disableMonkeyPatch();
    const stack = generateStack()
    const useRecord = { pattern: this.source, subject, stack, funcName: 'RegExp#exec', def: false };
    outputUsageRecord(useRecord);
    const result = this.innerExec(subject);
    // this.enableMonkeyPatch(exec, test);
    return result
  }

  RegExp.prototype.innerMatch = RegExp.prototype[Symbol.match];
  RegExp.prototype[Symbol.match] = function (subject) {
    const [exec, test] = this.disableMonkeyPatch();
    const stack = generateStack()
    const useRecord = { pattern: this.source, subject, stack, funcName: 'RegExp#match', def: false };
    outputUsageRecord(useRecord);
    const result = this.innerMatch(subject);
    this.enableMonkeyPatch(exec, test);
    return result;
  }

  RegExp.prototype.innerMatchAll = RegExp.prototype[Symbol.matchAll];
  RegExp.prototype[Symbol.matchAll] = function (subject) {
    const [exec, test] = this.disableMonkeyPatch();
    const stack = generateStack()
    const useRecord = { pattern: this.source, subject, stack, funcName: 'RegExp#matchAll', def: false };
    outputUsageRecord(useRecord);
    const result = this.innerMatchAll(subject);
    this.enableMonkeyPatch(exec, test);
    return result;
  }

  RegExp.prototype.innerReplace = RegExp.prototype[Symbol.replace];
  RegExp.prototype[Symbol.replace] = function (subject, replacement) {
    const [exec, test] = this.disableMonkeyPatch();
    const stack = generateStack()
    const useRecord = { pattern: this.source, subject, stack, funcName: 'RegExp#replace', def: false };
    outputUsageRecord(useRecord);
    const result = this.innerReplace(subject, replacement);
    this.enableMonkeyPatch(exec, test);
    return result;
  }

  RegExp.prototype.innerSearch = RegExp.prototype[Symbol.search];
  RegExp.prototype[Symbol.search] = function (subject, replacement) {
    const [exec, test] = this.disableMonkeyPatch();
    const stack = generateStack()
    const useRecord = { pattern: this.source, subject, stack, funcName: 'RegExp#search', def: false };
    outputUsageRecord(useRecord);
    const result = this.innerSearch(subject, replacement);
    this.enableMonkeyPatch(exec, test);
    return result;
  }

  RegExp.prototype.innerSplit = RegExp.prototype[Symbol.split];
  RegExp.prototype[Symbol.split] = function (subject, delim) {
    const [exec, test] = this.disableMonkeyPatch();
    const stack = generateStack()
    const useRecord = { pattern: this.source, subject, stack, funcName: 'RegExp#split', def: false };
    outputUsageRecord(useRecord);
    const result = this.innerSplit(subject, delim);
    this.enableMonkeyPatch(exec, test);
    return result;
  }
}