# MV Feistel 32 App

This folder contains the Flask app for the 32-bit multivariate Feistel cipher.

The polynomial systems used here are 4-bit Boolean polynomial systems generated from Gröbner basis compositions and selected using the shuffle algorithm developed in the third-year project.

## Requirements

Use Python 3.11+.

## Quick start

From this folder:

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open the browser at:

```text
http://127.0.0.1:5000/
```

## What you can do

- enter a plaintext word or binary value
- choose the number of rounds
- encrypt the value
- decrypt the ciphertext using the stored round metadata
- view the polynomial file chosen for each round

## How encryption works

The app uses a 32-bit Feistel cipher built from 4-bit polynomial systems.

1. The plaintext is converted into a 32-bit binary block.
2. The block is split into a left half and a right half.
3. For each round, the right half is divided into four 4-bit chunks.
4. The app selects four polynomial systems from the Gröbner-basis composition set and applies the shuffle algorithm from the third-year project to choose the active systems for that round.
5. Each 4-bit chunk is transformed by its selected polynomial system.
6. The four outputs are concatenated into a 16-bit round function output and XORed with the left half.
7. The updated state continues to the next round.
8. After the final round, the ciphertext is returned together with the per-round metadata.

Each round stores the polynomial file used for that round so the same schedule can later be reversed.

## How decryption works

Decryption uses the same round metadata that was returned during encryption.

1. The ciphertext is split into the same left/right Feistel halves.
2. The round function output from the stored round metadata is applied in reverse order.
3. The inverse Feistel step restores the previous left and right values.
4. After the final reverse round, the original plaintext is recovered.

This is why the app keeps the round outputs and selected polynomial metadata when encrypting: without them, the ciphertext cannot be reversed reliably. The round-level metadata is especially important because the system is using four 4-bit polynomial systems per round, chosen from the Gröbner-basis composition data and shuffled according to the project algorithm.

## Notes

The app loads polynomial systems from the app/data/polynomials folder.
If you move the app folder to another machine, keep the data folder together with it.
