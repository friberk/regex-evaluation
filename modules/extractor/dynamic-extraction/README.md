# dynamic-extraction

Provides an interface for dynamically extracting resources. The main responsibility is to pull out strings that are evalauted against regexes.

Each dynamic extractor implements a series of lifecycle hooks. They are:
- `pre_install`: run code before installing external dependencies
- `install_deps`: install external dependencies
- `build_pkg`: perform compile step
- `run_test_suite`: run the package's test suite

Here's how this looks for JS:
- `pre_install`: turn off linters and other preprocessing steps
- `install_deps`: run `npm install`
- `build_pkg`: run `npm run build`. If this doesn't work, don't worry
- `run_test_suite`: run the package's test suite with `npm test`

The JS example has additional features such as:
- configuring a fake `HOME` directory (npm installs stuff in HOME, so it might be helpful to change this directory to a cache dir)
- timeouts for `install` and `test`
- an example limit to limit how many examples we collect for each regex

Note: this module works on a directory that has already been cloned. Don't clone in any of the dynamic extractor steps.
 
