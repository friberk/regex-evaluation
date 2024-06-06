package edu.purdue.dualitylab.evaluation.commands;

import java.util.concurrent.Callable;

/**
 * General command type used for sub command delegation
 * @param <ArgsT> The type of the arguments class to be provided to this command
 * @param <ResultT> An optional result type to produce
 */
public abstract class AbstractCommand<ArgsT, ResultT> implements Callable<ResultT> {
    protected final ArgsT args;

    protected AbstractCommand(ArgsT args) {
        this.args = args;
    }
}
