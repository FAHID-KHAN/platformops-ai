from platformops.providers.kubernetes.api import KubernetesApiProvider


def test_decode_log_text_handles_bytes():
    provider = KubernetesApiProvider()

    text = provider._decode_log_text(b"jenkins is fully up and running\n")

    assert text == "jenkins is fully up and running\n"


def test_decode_log_text_handles_strings():
    provider = KubernetesApiProvider()

    text = provider._decode_log_text("plain log line")

    assert text == "plain log line"

