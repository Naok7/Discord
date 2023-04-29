const COPY = "content_copy";
const COPIED = "done";

const copy = async (obj) => {
    // <span class="copy"><span class="material-icons">{{text}}</span></span>
    await navigator.clipboard.writeText(obj.children[1].innerText).then(
        () => {
            let icon = obj.children[0].children[0];
            icon.textContent = COPIED;
            setTimeout(() => (icon.textContent = COPY), 2500);
        },
        (r) => alert(DPY_TRANSLATIONS.copy_code_error + '\n' + r.toString())
    );
};

document.addEventListener("DOMContentLoaded", () => {
    let allCodeblocks = document.querySelectorAll("div[class='highlight']");

    for (let codeblock of allCodeblocks) {
        codeblock.parentNode.className += " relative-copy";
        let copyEl = document.createElement("span");
        copyEl.addEventListener('click', () => copy(codeblock));
        copyEl.className = "copy";
        copyEl.setAttribute("aria-label", DPY_TRANSLATIONS.copy_code);
        copyEl.setAttribute("title", DPY_TRANSLATIONS.copy_code);

        let copyIcon = document.createElement("span");
        copyIcon.className = "material-icons";
        copyIcon.textContent = COPY;
        copyEl.append(copyIcon);

        codeblock.prepend(copyEl);
    }
});
