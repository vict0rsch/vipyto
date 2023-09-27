import subprocess
import re
import os

from vipyto import print
from vipyto.cmd import run_command
from vipyto.path import resolve

IMPORTS_OK = False
try:
    import torch
    import random
    import numpy as np

    IMPORTS_OK = True
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
