const input = document.getElementById('user-input');
const answerBox = document.getElementById('answer-box');
const sendBtn = document.getElementById('send-btn');
const secondsPerChar = 0.01;

// Helper to send question
async function askSocrates() {
  const question = input.value.trim();
  if (!question) return;

  // Show talking animation
  answerBox.textContent = "Thinking...";

  try {
    const res = await fetch('/prompt', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ message: question })
    });

    const data = await res.json();

    let answer = data.answer || "No answer";
    input.value = '';
    let pos = 0
    let timer = setInterval(() => {
        if (pos+1 <= answer.length) {
          pos += 1;
        } else {
          clearInterval(timer);
          return;
        }
        answerBox.textContent = answer.slice(0, pos);
      }
    , secondsPerChar * 1000);
  } catch (err) {
    console.error(err);
    answerBox.textContent = "Couldn't reach model.";
  }
}

// Send on Enter or Button click
input.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') askSocrates();
});
sendBtn.addEventListener('click', askSocrates);
