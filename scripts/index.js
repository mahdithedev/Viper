async function main() {

    const res = await fetch("http://localhost:3000/api/test");
    const {message} = await res.json();

    const div = document.createElement("div");
    div.innerText = message;
    document.body.appendChild(div);

};

main();