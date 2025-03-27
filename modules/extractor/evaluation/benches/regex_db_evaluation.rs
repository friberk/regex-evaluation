use std::fs;
use std::fs::File;
use std::io::{Read, Write};
use criterion::{Criterion, criterion_group, criterion_main};
use rand::Rng;
use regex::Regex;
use regex_automata::dfa::Automaton;
use regex_automata::dfa::dense::DFA;
use regex_automata::Input;

const SHORT_REGEX: &str = r"^\w+$";
const SHORT_SUBJECT: &str = "hello";

const LONG_REGEX: &str = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$";

const LONG_SUBJECT: &str = "this.is.a.really.long_email_address@somesuperlongcrazydomain.co.uk";

fn benchmark_short_regex_compile_and_evaluate_in_loop(criterion: &mut Criterion) {
    criterion.bench_function("compile short regex and evaluate in loop", |bencher| {
        bencher.iter(move || {
            let regex = Regex::new(SHORT_REGEX).unwrap();
            regex.is_match(SHORT_SUBJECT);
        });
    });
}

fn load_short_regex_from_disk_and_use(criterion: &mut Criterion) {

    let regex = regex_automata::dfa::regex::Regex::new(SHORT_REGEX).unwrap();
    let (dfa_bytes, _) = regex.forward().to_bytes_native_endian();

    let rng = &mut rand::thread_rng();
    let suffix: usize = rng.gen();
    let path = std::env::temp_dir().join(format!("temp-regex-dfa-{}.bin", suffix));
    {
        let mut output = File::create(&path).unwrap();
        output.write_all(&dfa_bytes).unwrap();
    }

    criterion.bench_function(
        "compile short regex once and pull from disk",
        |bencher| {
            bencher.iter(|| {
                let mut bytes = Vec::<u8>::new();
                let mut file = File::open(&path).unwrap();
                file.read_to_end(&mut bytes).unwrap();

                let dfa = DFA::from_bytes(&bytes).unwrap().0;
                dfa.try_search_fwd(&Input::from(SHORT_SUBJECT)).unwrap();
            })
        }
    );
    
    fs::remove_file(path).unwrap();
}

fn benchmark_long_regex_compile_and_evaluate_in_loop(criterion: &mut Criterion) {
    criterion.bench_function("compile long regex and evaluate in loop", |bencher| {
        bencher.iter(move || {
            let regex = Regex::new(LONG_REGEX).unwrap();
            regex.is_match(LONG_SUBJECT);
        });
    });
}

fn load_long_regex_from_disk_and_use(criterion: &mut Criterion) {

    let regex = regex_automata::dfa::regex::Regex::new(LONG_REGEX).unwrap();
    let (dfa_bytes, _) = regex.forward().to_bytes_native_endian();

    let rng = &mut rand::thread_rng();
    let suffix: usize = rng.gen();
    let path = std::env::temp_dir().join(format!("temp-regex-dfa-{}.bin", suffix));
    
    {
        let mut output = File::create(&path).unwrap();
        output.write_all(&dfa_bytes).unwrap();
    }

    criterion.bench_function(
        "compile long regex once and pull from disk",
        |bencher| {
            bencher.iter(|| {
                let mut bytes = Vec::<u8>::new();
                let mut file = File::open(&path).unwrap();
                file.read_to_end(&mut bytes).unwrap();

                let dfa = DFA::from_bytes(&bytes).unwrap().0;
                dfa.try_search_fwd(&Input::from(LONG_SUBJECT)).unwrap();
            })
        }
    );

    fs::remove_file(path).unwrap();
}

criterion_group!(
    benches,
    benchmark_short_regex_compile_and_evaluate_in_loop,
    load_short_regex_from_disk_and_use,
    benchmark_long_regex_compile_and_evaluate_in_loop,
    load_long_regex_from_disk_and_use
);
criterion_main!(benches);
