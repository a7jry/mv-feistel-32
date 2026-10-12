import json
import random
from pathlib import Path

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

APP_ROOT = Path(__file__).resolve().parent

POLYNOMIAL_SYSTEMS_DIRS = [
    APP_ROOT / "data" / "polynomials",
    APP_ROOT / "data" / "polynomial_systems",
    APP_ROOT / "data" / "polynomial systems",
]


# ============================================================
# POLYNOMIAL DATA LOADING
# ============================================================

def load_polynomial_systems():
    """Load JSON polynomial systems from the app data folders."""

    systems = []
    seen_files = set()

    for directory in POLYNOMIAL_SYSTEMS_DIRS:
        if not directory.exists():
            continue

        for path in sorted(directory.glob("*.json")):
            resolved_path = path.resolve()

            if resolved_path in seen_files:
                continue

            seen_files.add(resolved_path)

            try:
                with path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)

                polynomials = payload.get("polynomials", [])

                if len(polynomials) != 4:
                    print(f"Skipping {path.name}: expected 4 polynomials.")
                    continue

                systems.append({
                    "source_file": path.name,
                    "polynomials": polynomials,
                })

            except (OSError, json.JSONDecodeError) as error:
                print(f"Could not load {path}: {error}")

    if not systems:
        raise RuntimeError(
            "No valid polynomial systems found. "
            "Check the JSON files in app/data/."
        )

    return systems


POLYNOMIAL_SYSTEMS = load_polynomial_systems()


# ============================================================
# BOOLEAN POLYNOMIAL EVALUATION
# ============================================================

def evaluate_polynomial_expression(expression, variable_values):
    """Evaluate a Boolean polynomial over GF(2)."""

    normalized = expression.replace(" ", "")

    if not normalized:
        return 0

    total = 0

    for term in normalized.split("+"):
        if not term:
            continue

        product_value = 1

        for factor in term.split("*"):
            if factor == "1":
                continue

            if "^" in factor:
                variable_name, exponent = factor.split("^", 1)
                exponent = int(exponent)

                if exponent == 0:
                    continue

                variable_value = variable_values.get(variable_name, 0)

                if variable_value == 0:
                    product_value = 0
                    break

            else:
                variable_value = variable_values.get(factor, 0)

                if variable_value == 0:
                    product_value = 0
                    break

        total ^= product_value

    return total


def multivariate_4bit(bits, polynomial_system):
    """Transform a 4-bit input into a 4-bit output."""

    if len(bits) != 4 or any(bit not in "01" for bit in bits):
        raise ValueError("Input must contain exactly 4 binary bits.")

    variable_values = {f"x{i}": int(bit) for i, bit in enumerate(bits)}
    polynomials = polynomial_system["polynomials"]

    output = "".join(
        str(evaluate_polynomial_expression(poly, variable_values))
        for poly in polynomials
    )

    return output


# ============================================================
# BIT OPERATIONS
# ============================================================

def validate_bits(value, length, name, allow_shorter=False):
    if any(bit not in "01" for bit in value):
        raise ValueError(f"{name} must contain only 0 and 1.")

    if len(value) > length:
        raise ValueError(f"{name} must contain at most {length} bits.")

    if not allow_shorter and len(value) != length:
        raise ValueError(f"{name} must contain exactly {length} bits.")


def normalize_bits(value, length, name, allow_shorter=False):
    validate_bits(value, length, name, allow_shorter)
    return value.zfill(length)


def text_to_bits(value, length=32):
    """Convert text or a binary string to a fixed-length bitstring."""

    if value == "":
        return "0" * length

    if all(char in "01" for char in value):
        bits = value
        if len(bits) > length:
            return bits[:length]
        return bits.zfill(length)

    bits = "".join(f"{ord(char):08b}" for char in value)

    if len(bits) > length:
        return bits[:length]

    return bits.zfill(length)


def xor_bits(a, b):
    if len(a) != len(b):
        raise ValueError("XOR inputs must have equal lengths.")

    return "".join("1" if x != y else "0" for x, y in zip(a, b))


def bits_to_ascii_word(bits):
    """Convert a bitstring to printable ASCII, using '.' for other bytes."""

    if not bits:
        return ""

    if any(bit not in "01" for bit in bits):
        raise ValueError("Bit string must contain only 0 and 1.")

    padded = bits.zfill(((len(bits) + 7) // 8) * 8)
    characters = []

    for i in range(0, len(padded), 8):
        value = int(padded[i:i + 8], 2)

        if 32 <= value <= 126:
            characters.append(chr(value))
        else:
            characters.append(".")

    return "".join(characters)


# ============================================================
# FEISTEL ROUND FUNCTION
# ============================================================

def round_function(right, round_index=0, polynomial_systems=None):
    """Transform a 16-bit right half using four polynomial systems."""

    if len(right) != 16 or any(bit not in "01" for bit in right):
        raise ValueError("Round input must contain exactly 16 bits.")

    if polynomial_systems is None:
        if len(POLYNOMIAL_SYSTEMS) < 4:
            raise ValueError("At least four systems are required.")

        chosen_systems = random.sample(POLYNOMIAL_SYSTEMS, 4)
    else:
        chosen_systems = polynomial_systems

    if len(chosen_systems) != 4:
        raise ValueError("Exactly four polynomial systems are required.")

    transformations = []
    outputs = []

    for i, system in enumerate(chosen_systems):
        chunk = right[i * 4:(i + 1) * 4]
        output = multivariate_4bit(chunk, system)

        outputs.append(output)

        transformations.append({
            "input": chunk,
            "output": output,
            "polynomial_file": system["source_file"],
        })

    return "".join(outputs), transformations, chosen_systems


# ============================================================
# FEISTEL ENCRYPTION
# ============================================================

def encrypt_32bit(plaintext, master_key="", rounds=8):
    """Encrypt one 32-bit block using a Feistel network."""

    if not isinstance(rounds, int) or not 1 <= rounds <= 32:
        raise ValueError("Rounds must be between 1 and 32.")

    if len(POLYNOMIAL_SYSTEMS) < 4:
        raise ValueError("At least four polynomial systems are required.")

    plaintext = text_to_bits(plaintext, length=32)

    left = plaintext[:16]
    right = plaintext[16:]

    states = []

    for i in range(rounds):
        f_input = right

        chosen_systems = random.sample(POLYNOMIAL_SYSTEMS, 4)
        f_output, transformations, _ = round_function(
            right,
            round_index=i,
            polynomial_systems=chosen_systems,
        )

        new_left = right
        new_right = xor_bits(left, f_output)

        states.append({
            "round": i + 1,
            "left": left,
            "right": right,
            "f_input": f_input,
            "transformations": transformations,
            "f_output": f_output,
            "polynomial_file": ", ".join(system["source_file"] for system in chosen_systems),
            "new_left": new_left,
            "new_right": new_right,
        })

        left = new_left
        right = new_right

    ciphertext = right + left

    return {
        "plaintext": plaintext,
        "plaintext_word": int(plaintext, 2),
        "plaintext_ascii": bits_to_ascii_word(plaintext),
        "ciphertext": ciphertext,
        "ciphertext_word": int(ciphertext, 2),
        "ciphertext_ascii": bits_to_ascii_word(ciphertext),
        "rounds": states,
    }


# ============================================================
# FEISTEL DECRYPTION
# ============================================================

def decrypt_32bit(ciphertext, rounds_data):
    """Recover the plaintext using the recorded round outputs."""

    if not rounds_data:
        raise ValueError("Encryption round metadata is required.")

    if not isinstance(ciphertext, str):
        ciphertext = str(ciphertext)

    if set(ciphertext) <= {"0", "1"}:
        ciphertext_bits = ciphertext
    else:
        ciphertext_bits = text_to_bits(ciphertext, length=32)

    if len(ciphertext_bits) != 32:
        raise ValueError("Ciphertext must be exactly 32 bits.")

    left = ciphertext_bits[16:]
    right = ciphertext_bits[:16]

    for state in reversed(rounds_data):
        f_output = state.get("f_output")

        if not isinstance(f_output, str) or len(f_output) != 16:
            raise ValueError("Invalid round function output in metadata.")

        previous_left = xor_bits(right, f_output)
        previous_right = left

        left = previous_left
        right = previous_right

    plaintext = left + right

    return {
        "plaintext": plaintext,
        "plaintext_word": int(plaintext, 2),
        "plaintext_ascii": bits_to_ascii_word(plaintext),
        "ciphertext": ciphertext_bits,
        "ciphertext_word": int(ciphertext_bits, 2),
        "ciphertext_ascii": bits_to_ascii_word(ciphertext_bits),
        "rounds": rounds_data,
    }


# ============================================================
# FLASK ROUTES
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/encrypt", methods=["POST"])
def encrypt():
    data = request.get_json(silent=True) or {}

    plaintext = data.get("plaintext", "")
    rounds = data.get("rounds", 8)

    try:
        rounds = int(rounds)

        result = encrypt_32bit(
            plaintext,
            rounds=rounds,
        )

        return jsonify({
            "success": True,
            **result,
        })

    except (ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 400


@app.route("/decrypt", methods=["POST"])
def decrypt():
    data = request.get_json(silent=True) or {}

    ciphertext = data.get("ciphertext", "")
    rounds_data = data.get("rounds", [])

    try:
        result = decrypt_32bit(ciphertext, rounds_data)

        return jsonify({
            "success": True,
            **result,
        })

    except (ValueError, TypeError, KeyError) as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 400


# ============================================================
# RUN APP
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
