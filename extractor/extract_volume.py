import argparse
import glob
import multiprocessing
from functools import partial
from pathlib import Path

import librosa
import numpy
import tqdm

from acoustic_feature_extractor.data import Wave
from acoustic_feature_extractor.utility.json_utility import save_arguments


def process(
        path: Path,
        output_directory: Path,
        sampling_rate: int,
        frame_length: int,
        hop_length: int,
        top_db: int,
        normalize: bool,
):
    assert sampling_rate % hop_length == 0

    w = Wave.load(path, sampling_rate).wave

    mse = librosa.feature.rms(w, frame_length=frame_length, hop_length=hop_length) ** 2
    array = librosa.power_to_db(mse.squeeze(), top_db=top_db)[:-1]

    if normalize:
        array = numpy.clip((array - array.max()) / top_db + 1, 0, 1)

    rate = sampling_rate // hop_length

    out = output_directory / (path.stem + '.npy')
    numpy.save(str(out), dict(array=array, rate=rate))


def extract_volume(
        input_glob,
        output_directory: Path,
        sampling_rate: int,
        frame_length: int,
        hop_length: int,
        top_db: int,
        normalize: bool,
):
    output_directory.mkdir(exist_ok=True)
    save_arguments(locals(), output_directory / 'arguments.json')

    paths = [Path(p) for p in glob.glob(str(input_glob))]
    _process = partial(
        process,
        output_directory=output_directory,
        sampling_rate=sampling_rate,
        frame_length=frame_length,
        hop_length=hop_length,
        top_db=top_db,
        normalize=normalize,
    )

    pool = multiprocessing.Pool()
    list(tqdm.tqdm(pool.imap(_process, paths), total=len(paths)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_glob', '-ig', required=True)
    parser.add_argument('--output_directory', '-od', type=Path, required=True)
    parser.add_argument('--sampling_rate', '-sr', type=int, required=True)
    parser.add_argument('--frame_length', '-fl', type=int, default=800)
    parser.add_argument('--hop_length', '-hl', type=int, default=200)
    parser.add_argument('--top_db', '-td', type=int, default=80)
    parser.add_argument('--normalize', '-n', action='store_true')
    extract_volume(**vars(parser.parse_args()))


if __name__ == '__main__':
    main()
