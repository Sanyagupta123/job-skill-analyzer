(() => {
  const form = document.querySelector("#analyzer-form");
  const jobInput = document.querySelector("#job-description");
  const skillsInput = document.querySelector("#user-skills");
  const analyzeButton = document.querySelector("#analyze-button");
  const statusMessage = document.querySelector("#status-message");
  const results = document.querySelector("#results");
  const maxLength = Number(jobInput.maxLength);
  let latestResult = null;

  for (const input of [jobInput, skillsInput]) {
    const count = document.querySelector(`[data-count-for="${input.id}"]`);
    input.addEventListener("input", () => {
      count.textContent = `${input.value.length.toLocaleString()} / ${maxLength.toLocaleString()}`;
    });
  }

  function showError(message) {
    statusMessage.textContent = message;
    statusMessage.hidden = false;
    statusMessage.className = "status-message";
    statusMessage.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function renderList(element, names, emptyMessage) {
    element.replaceChildren();
    if (!names.length) {
      const item = document.createElement("li");
      item.className = "empty-list";
      item.textContent = emptyMessage;
      element.append(item);
      return;
    }
    for (const name of names) {
      const item = document.createElement("li");
      item.textContent = name;
      element.append(item);
    }
  }

  function renderCategories(categories) {
    const container = document.querySelector("#candidate-skills");
    container.replaceChildren();
    const entries = Object.entries(categories);
    if (!entries.length) {
      const empty = document.createElement("p");
      empty.className = "empty-list";
      empty.textContent = "No skills were detected in the job description.";
      container.append(empty);
      return;
    }

    for (const [category, names] of entries) {
      const group = document.createElement("section");
      group.className = "category-group";
      const heading = document.createElement("h4");
      heading.textContent = category;
      const list = document.createElement("div");
      list.className = "category-skills";
      for (const name of names) {
        const chip = document.createElement("span");
        chip.className = "skill-chip";
        chip.textContent = name;
        list.append(chip);
      }
      group.append(heading, list);
      container.append(group);
    }
  }

  function renderPriority(items) {
    const list = document.querySelector("#priority-list");
    list.replaceChildren();
    if (!items.length) {
      const item = document.createElement("li");
      item.className = "empty-list";
      item.textContent = "No missing skills to prioritize.";
      list.append(item);
      return;
    }

    for (const item of items) {
      const row = document.createElement("li");
      row.className = "priority-item";
      row.innerHTML = `
        <div>
          <strong>${item.skill}</strong>
          <span>${item.category}</span>
        </div>
        <span class="priority-badge priority-${item.priority.toLowerCase()}">${item.priority}</span>
      `;
      list.append(row);
    }
  }

  function renderResult(data) {
    latestResult = data;
    document.querySelector("#match-percentage").textContent = `${Number(data.match_percentage).toFixed(2)}%`;
    document.querySelector("#detected-count").textContent = data.detected_skills.length;
    document.querySelector("#matched-count").textContent = data.matched_skill_count;
    document.querySelector("#missing-count").textContent = data.missing_skill_count;

    const note = data.required_skill_count
      ? `${data.required_skill_count} role skills were detected from the job description.`
      : "No skill catalog matches were found in the job description.";
    document.querySelector("#score-note").textContent = note;

    renderList(document.querySelector("#matched-list"), data.matched_skills, "No matching skills found yet.");
    renderList(document.querySelector("#missing-list"), data.missing_skills, "No skill gaps detected.");
    renderCategories(data.categories || data.required_categories || {});
    renderPriority(data.priority || []);
    results.hidden = false;
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    statusMessage.hidden = true;
    results.hidden = true;

    const jobDescription = jobInput.value.trim();
    const userSkills = skillsInput.value.trim();

    if (!jobDescription || !userSkills) {
      showError("Please provide both a job description and your known skills.");
      return;
    }

    analyzeButton.disabled = true;
    analyzeButton.querySelector("span:first-child").textContent = "Analyzing…";

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_description: jobDescription,
          user_skills: userSkills,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Analysis failed. Please try again.");
      }
      renderResult(data);
    } catch (error) {
      showError(error instanceof TypeError ? "Could not reach the analyzer. Check your connection and try again." : error.message);
    } finally {
      analyzeButton.disabled = false;
      analyzeButton.querySelector("span:first-child").textContent = "Analyze job";
    }
  });

  function summaryText() {
    if (!latestResult) return "";
    return [
      `Job Skill Analyzer — ${Number(latestResult.match_percentage).toFixed(2)}% match score`,
      `Detected skills (${latestResult.required_skill_count}): ${latestResult.detected_skills.join(", ") || "None"}`,
      `Matched skills (${latestResult.matched_skill_count}): ${latestResult.matched_skills.join(", ") || "None"}`,
      `Missing skills (${latestResult.missing_skill_count}): ${latestResult.missing_skills.join(", ") || "None"}`,
      "",
      "Rule-based comparison; use this as a starting point for learning and interviewing prep.",
    ].join("\n");
  }

  document.querySelector("#copy-button").addEventListener("click", async () => {
    if (!latestResult) return;
    try {
      await navigator.clipboard.writeText(summaryText());
      statusMessage.textContent = "Summary copied to clipboard.";
      statusMessage.className = "status-message success-message";
      statusMessage.hidden = false;
    } catch (_error) {
      showError("Clipboard access is unavailable. Use the Download button instead.");
    }
  });

  document.querySelector("#download-button").addEventListener("click", () => {
    if (!latestResult) return;
    const blob = new Blob([summaryText()], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "job-skill-analysis.txt";
    link.click();
    URL.revokeObjectURL(url);
  });

  document.querySelector("#reset-button").addEventListener("click", () => {
    form.reset();
    for (const input of [jobInput, skillsInput]) {
      document.querySelector(`[data-count-for="${input.id}"]`).textContent = `0 / ${maxLength.toLocaleString()}`;
    }
    latestResult = null;
    results.hidden = true;
    statusMessage.hidden = true;
    jobInput.focus();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
})();
