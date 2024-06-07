package edu.purdue.dualitylab.evaluation.commands;

import edu.purdue.dualitylab.evaluation.args.RootArgs;

import java.util.concurrent.Callable;

/**
 * General command type used for sub command delegation
 * @param <ArgsT> The type of the arguments class to be provided to this command
 * @param <ResultT> An optional result type to produce
 */
public abstract class AbstractCommand<ArgsT, ResultT> implements Callable<ResultT> {
    protected final RootArgs rootArgs;
    protected final ArgsT args;

    protected AbstractCommand(RootArgs rootArgs, ArgsT args) {
        this.rootArgs = rootArgs;
        this.args = args;
    }
}
