"""
Training utilities for PyTorch deep learning code.

.. warning::

    Requires torch and numpy to be installed.

For instance if you don't want to always manually match the number of workers
in your dataloaders to the number of cpus available on your machine (for example
when you vary the number of cpus available to your job on a SLURM cluster), you can
just use :py:func:`~vipyto.train.get_num_workers_from_cpus` to get the number of
CPUs (divided by the number of GPUs if GPUs are available):

.. code-block:: python

    from vipyto.train import get_num_workers_from_cpus, set_seeds

    # parse your args
    ...
    args = parse_args()
    # initialize a generic config dict
    config = {
        "workers": 2,
    }

    ...
    if not args.keep_workers:
        config["workers"] = get_num_workers_from_cpus()

    ...

    set_seeds(args.seed) # set numpy, random, torch and cuda seeds
                         # and set cudnn to deterministic mode for reproducibility

"""

import os
import re
import subprocess

from vipyto import print
from vipyto.cmd import run_command
from vipyto.path import resolve

try:
    import random

    import numpy as np
    import torch

except ImportError:
    print(
        "\n[bold red]💥 torch and numpy must be"
        + " installed to use vipyto.train[/bold red]\n",
    )
    raise


def set_seeds(seed=0):
    """
    Set seeds for torch, random, numpy and cuda.

    Args:
        seed (int, optional): Seed. Defaults to 0.
    """
    seed = 0
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True


def count_cpus(job_id=None):
    """
    Count the number of cpus available on the system, parsing SLURM info if available.

    Args:
        job_id (int, optional): SLURM_JOB_ID to count cpus for. Will be read
            from the environment variable if none is provided. Is ignored if no
            SLURM info is available (on a local machine for instance). Defaults to None.

    Returns:
        int: Number of cpus available for this process.
    """
    cpus = None
    if job_id is None:
        job_id = os.environ.get("SLURM_JOB_ID")
    if job_id:
        try:
            slurm_cpus = run_command(f"squeue --job {job_id} -o %c").split("\n")[1]
            cpus = int(slurm_cpus)
        except subprocess.CalledProcessError:
            cpus = os.cpu_count()
    else:
        cpus = os.cpu_count()

    return cpus


def count_gpus(job_id=None):
    """
    Count the number of gpus available on the system, parsing SLURM info if available.
    Otherwise, returns the number of gpus available on the system according to torch.

    Args:
        job_id (str|int, optional): SLURM_JOB_ID to count gpus for. Will be read
            from the environment variable if none is provided. Is ignored if no
            SLURM info is available (on a local machine for instance). Defaults to None.

    Returns:
        int: Number of gpus available for this process.
    """
    gpus = 0
    if job_id is None:
        job_id = os.environ.get("SLURM_JOB_ID")
    if job_id:
        try:
            slurm_gpus = run_command(f"squeue --job {job_id} -o %b").split("\n")[1]
            gpus = re.findall(r".*(\d+)", slurm_gpus) or 0
            gpus = int(gpus[0]) if gpus != 0 else gpus
        except subprocess.CalledProcessError:
            gpus = torch.cuda.device_count()
    else:
        gpus = torch.cuda.device_count()

    return gpus


def get_num_workers_from_cpus(job_id=None, verbose=False):
    """
    Get the number of workers to use for a dataloader, based on the number of cpus
    available on the machine (reads SLURM info if available).

    Number of workers is set to the number of cpus minus one if no gpus are available,
    or to the number of cpus divided by the number of gpus if gpus are available.

    Args:
        job_id (int, optional): SLURM_JOB_ID to count cpus for. Will be read
            from the environment variable if none is provided. Is ignored if no
            SLURM info is available (on a local machine for instance). Defaults to None.
        verbose (bool, optional): Print the number of workers that will be used.
            Defaults to False.

    Returns:
        _type_: _description_
    """
    if job_id is None:
        job_id = os.environ.get("SLURM_JOB_ID")
    cpus = count_cpus(job_id)
    gpus = count_gpus(job_id)
    if cpus is not None:
        if gpus == 0:
            workers = cpus - 1
        else:
            workers = cpus // gpus
    if verbose:
        print(f"Using {workers} workers (cpus: {cpus}, gpus: {gpus})")
    return workers


def slurm_tmpdir(job_id=None):
    """
    Returns the path to the slurm tmpdir if it exists, otherwise returns None.
    Useful if the $SLURM_TMPDIR is not guaranteed to exist.

    Args:
        job_id (str|int, optional): SLURM_JOB_ID to count gpus for. Will be read
            from the environment variable if none is provided. Is ignored if no
            SLURM info is available (on a local machine for instance). Defaults to None.

    Returns:
        Optional[str]: The path to the slurm tmpdir or None
    """
    job_id = job_id or os.environ.get("SLURM_JOB_ID")
    if job_id is not None:
        return resolve(f"/Tmp/slurm.{job_id}.0")
