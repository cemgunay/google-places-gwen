function getDivContents() {
    let titles = [];
    const divs = document.getElementsByClassName('fontHeadlineSmall rZF81c');

    for (let div of divs) {
        if (div.textContent) {
            titles.push(`"${div.textContent}"`); // Wrap each title in double quotes
        }
    }

    return titles;
}

const allTitles = getDivContents();
console.log(allTitles);

let csvContent = "data:text/csv;charset=utf-8," + allTitles.join("\n");

const encodedUri = encodeURI(csvContent);
const link = document.createElement("a");
link.setAttribute("href", encodedUri);
link.setAttribute("download", "titles.csv");
document.body.appendChild(link);

link.click();