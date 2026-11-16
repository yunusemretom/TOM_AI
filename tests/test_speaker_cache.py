import torch

from tom.voice.speaker_cache import SpeakerLatents, cache_key, load_or_compute

PARAMS = {"gpt_cond_len": 30, "gpt_cond_chunk_len": 4, "max_ref_len": 30, "sound_norm_refs": False}


def _ref(tmp_path, name, data):
    p = tmp_path / name
    p.write_bytes(data)
    return p


def test_cache_key_depends_on_audio_content_not_name(tmp_path):
    a = _ref(tmp_path, "a.wav", b"ses-1")
    b = _ref(tmp_path, "b.wav", b"ses-1")
    c = _ref(tmp_path, "c.wav", b"ses-2")
    assert cache_key([a], PARAMS, "m") == cache_key([b], PARAMS, "m")
    assert cache_key([a], PARAMS, "m") != cache_key([c], PARAMS, "m")


def test_cache_key_depends_on_params_and_model(tmp_path):
    a = _ref(tmp_path, "a.wav", b"ses-1")
    assert cache_key([a], PARAMS, "m1") != cache_key([a], PARAMS, "m2")
    assert cache_key([a], PARAMS, "m") != cache_key([a], {**PARAMS, "gpt_cond_len": 6}, "m")


def test_load_or_compute_computes_once_then_reads_file(tmp_path):
    calls = []

    def compute():
        calls.append(1)
        return SpeakerLatents(torch.ones(1, 32, 1024), torch.full((1, 512, 1), 2.0))

    lat1, hit1 = load_or_compute(tmp_path, "ugur", "abc", compute)
    lat2, hit2 = load_or_compute(tmp_path, "ugur", "abc", compute)

    assert (hit1, hit2) == (False, True)
    assert len(calls) == 1
    assert torch.equal(lat1.gpt_cond_latent, lat2.gpt_cond_latent)
    assert torch.equal(lat1.speaker_embedding, lat2.speaker_embedding)
    assert (tmp_path / "ugur-abc.pt").exists()


def test_load_or_compute_recomputes_for_new_key(tmp_path):
    calls = []

    def compute():
        calls.append(1)
        return SpeakerLatents(torch.zeros(1), torch.zeros(1))

    load_or_compute(tmp_path, "ugur", "k1", compute)
    load_or_compute(tmp_path, "ugur", "k2", compute)
    assert len(calls) == 2
