function textToBits(value) {
    const trimmed = value.trim();

    if (!trimmed) {
        return "";
    }

    if (/^[01]+$/.test(trimmed)) {
        return trimmed.padStart(32, "0").slice(0, 32);
    }

    const bits = Array.from(trimmed)
        .map((char) => char.charCodeAt(0).toString(2).padStart(8, "0"))
        .join("");

    return bits.slice(0, 32).padStart(32, "0");
}


const encryptButton =
    document.getElementById("encrypt-button");

const decryptButton =
    document.getElementById("decrypt-button");

const roundsInput =
    document.getElementById("rounds");

const roundsNumberInput =
    document.getElementById("rounds-number");

const roundsValue =
    document.getElementById("rounds-value");

let lastEncryptionResult = null;


function syncRounds(value) {

    const safeValue = Math.min(
        32,
        Math.max(1, Number(value) || 1)
    );

    roundsInput.value = safeValue;
    roundsNumberInput.value = safeValue;
    roundsValue.textContent = `${safeValue} round${safeValue === 1 ? "" : "s"}`;
}


roundsInput.addEventListener("input", (event) => {
    syncRounds(event.target.value);
});


roundsNumberInput.addEventListener("input", (event) => {
    syncRounds(event.target.value);
});


encryptButton.addEventListener("click", async () => {

    const plaintext =
        textToBits(document.getElementById("plaintext").value);

    const rounds =
        String(Number(roundsInput.value));


    try {

        const response = await fetch(
            "/encrypt",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    plaintext: plaintext,
                    rounds: rounds
                })
            }
        );


        const data =
            await response.json();


        if (!response.ok) {

            alert(data.error);

            return;
        }


        lastEncryptionResult = data;

        document
            .getElementById("result")
            .classList
            .remove("hidden");


        document
            .getElementById("rounds-section")
            .classList
            .remove("hidden");


        document
            .getElementById("ciphertext")
            .textContent =
                data.ciphertext;

        document
            .getElementById("decrypt-ciphertext")
            .value =
                data.ciphertext;

        document
            .getElementById("plaintext-word")
            .textContent =
                `${data.plaintext_word} (0x${data.plaintext_word.toString(16).toUpperCase()})`;

        document
            .getElementById("plaintext-ascii")
            .textContent =
                data.plaintext_ascii;

        document
            .getElementById("ciphertext-word")
            .textContent =
                `${data.ciphertext_word} (0x${data.ciphertext_word.toString(16).toUpperCase()})`;

        document
            .getElementById("ciphertext-ascii")
            .textContent =
                data.ciphertext_ascii;


        displayRounds(data.rounds);


    } catch (error) {

        console.error(error);

        alert(
            "Could not connect to Flask."
        );

    }

});


decryptButton.addEventListener("click", async () => {

    const ciphertext =
        document.getElementById("decrypt-ciphertext").value.trim();

    if (!ciphertext) {
        alert("Enter a ciphertext to decrypt.");
        return;
    }

    const rounds =
        lastEncryptionResult?.rounds || [];

    try {

        const response = await fetch(
            "/decrypt",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    ciphertext,
                    rounds
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            alert(data.error);
            return;
        }

        document.getElementById("decrypted-plaintext").textContent = data.plaintext;
        document.getElementById("decrypted-ascii").textContent = data.plaintext_ascii;
        document.getElementById("decryption-result").classList.remove("hidden");

    } catch (error) {
        console.error(error);
        alert("Could not decrypt the ciphertext.");
    }

});


function displayRounds(rounds) {

    const container =
        document.getElementById(
            "rounds-container"
        );


    container.innerHTML = "";


    rounds.forEach(state => {

        const round =
            document.createElement("div");

        round.className = "round";


        let transformations = "";


        state.transformations.forEach(
            (transformation, index) => {

                transformations += `

                    <div class="mv-box">

                        <div>
                            <span>
                                x${index}
                            </span>

                            <code>
                                ${transformation.input}
                            </code>
                        </div>

                        <div class="arrow">
                            ↓
                        </div>

                        <div>
                            <span>
                                f(x${index})
                            </span>

                            <code>
                                ${transformation.output}
                            </code>
                        </div>

                    </div>

                `;
            }
        );


        round.innerHTML = `

            <h3>
                Round ${state.round}
            </h3>

            <div class="step">
                <strong>
                    Polynomial Source
                </strong>
                <code class="large">
                    ${state.polynomial_file || "unknown"}
                </code>
            </div>


            <div class="step">

                <strong>
                    1. Feistel halves
                </strong>

                <div class="bits">

                    <div>
                        <span>L</span>
                        <code>${state.left}</code>
                    </div>

                    <div>
                        <span>R</span>
                        <code>${state.right}</code>
                    </div>

                </div>

            </div>


            <div class="step">

                <strong>
                    2. Apply the multivariate function to R
                </strong>

                <code class="large">
                    ${state.right}
                    &nbsp;→&nbsp;
                    ${state.f_output}
                </code>

            </div>


            <div class="step">

                <strong>
                    3. Apply the 8-bit polynomial system
                </strong>

                <div class="mv-grid">

                    ${transformations}

                </div>

            </div>


            <div class="step">

                <strong>
                    4. Combine the four outputs
                </strong>

                <code class="large">
                    ${state.f_output}
                </code>

            </div>


            <div class="step">

                <strong>
                    5. Feistel XOR
                </strong>

                <code class="large">
                    ${state.left}
                    &nbsp;⊕&nbsp;
                    ${state.f_output}
                    &nbsp;=&nbsp;
                    ${state.new_right}
                </code>

            </div>


            <div class="result-row">

                <div>
                    <span>L′</span>
                    <code>${state.new_left}</code>
                </div>

                <div>
                    <span>R′</span>
                    <code>${state.new_right}</code>
                </div>

            </div>

        `;


        container.appendChild(round);

    });

}