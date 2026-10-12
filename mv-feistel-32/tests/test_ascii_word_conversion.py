from app.app import (
    bits_to_ascii_word,
    decrypt_32bit,
    encrypt_32bit,
    load_polynomial_systems,
)


def test_load_polynomial_systems_reads_app_data_folder():
    systems = load_polynomial_systems()

    assert len(systems) > 0
    assert "polynomials" in systems[0]


def test_encrypt_32bit_uses_round_specific_polynomials():
    plaintext = "HELLO"
    master_key = "0" * 128

    result = encrypt_32bit(plaintext, master_key, 3)

    assert len(result["rounds"]) == 3
    assert all("polynomial_file" in round_state for round_state in result["rounds"])


def test_decrypt_32bit_round_trips_with_round_metadata():
    plaintext = "HELLO"
    master_key = "0" * 128

    encrypted = encrypt_32bit(plaintext, master_key, 3)
    decrypted = decrypt_32bit(encrypted["ciphertext"], encrypted["rounds"])

    assert decrypted["plaintext"] == encrypted["plaintext"]
    assert decrypted["ciphertext"] == encrypted["ciphertext"]


def test_bits_to_ascii_word_decodes_32_bit_block():
    bits = "01010100011001010111001101110100"

    assert bits_to_ascii_word(bits) == "Test"


def test_encrypt_32bit_includes_ascii_word_views():
    plaintext = "01010100011001010111001101110100"
    master_key = "0" * 128

    result = encrypt_32bit(plaintext, master_key, 1)

    assert result["plaintext_ascii"] == "Test"
    assert result["plaintext_word"] == int(plaintext, 2)
    assert "ciphertext_ascii" in result
    assert "ciphertext_word" in result


def test_encrypt_32bit_accepts_shorter_plaintext_inputs():
    plaintext = "1010"
    master_key = "0" * 128

    result = encrypt_32bit(plaintext, master_key, 1)

    assert result["plaintext"] == "00000000000000000000000000001010"
    assert result["plaintext_word"] == 10


def test_encrypt_32bit_accepts_word_input():
    plaintext = "HELLO"
    master_key = "0" * 128

    result = encrypt_32bit(plaintext, master_key, 1)

    assert result["plaintext"] == "01001000010001010100110001001100"
    assert result["plaintext_ascii"] == "HELL"
