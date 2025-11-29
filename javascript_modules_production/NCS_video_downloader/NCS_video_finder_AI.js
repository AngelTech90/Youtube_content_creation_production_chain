import ncs from "nocopyrightsounds-api";
import axios from "axios";
import fs from "fs/promises";
import dotenv from "dotenv";
import { GoogleGenerativeAI } from "@google/generative-ai";

dotenv.config();

const defaultDirectory = '../../in_production_content/downloaded_music/'

// Gemini setup
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({
    model: "gemini-2.0-flash",
    generationConfig: {
        temperature: 1.2,
        topK: 40,
        topP: 0.95
    }
});

// -----------------------------------------
// RATE LIMITING: 1 request every 4 seconds
// -----------------------------------------
let lastRequestTime = 0;
const REQUEST_DELAY = 4000; // 4 seconds = ~15 RPM max

async function rateLimitedGeminiCall(prompt) {
    const now = Date.now();
    const wait = Math.max(0, REQUEST_DELAY - (now - lastRequestTime));

    if (wait > 0) {
        console.log(`⏳ Waiting ${wait}ms to respect rate limits...`);
        await new Promise(res => setTimeout(res, wait));
    }

    lastRequestTime = Date.now();

    let attempts = 0;

    while (true) {
        try {
            const result = await model.generateContent(prompt);
            return result.response.text().trim();
        } catch (err) {
            // If 429 (Too Many Requests)
            if (err.status === 429) {
                attempts++;
                const backoff = Math.min(8000 * attempts, 30000); // cap at 30s
                console.log(`⚠️ Gemini rate limit hit. Waiting ${backoff}ms before retry...`);
                await new Promise(res => setTimeout(res, backoff));
                continue;
            }

            throw err;
        }
    }
}

// -----------------------------------------
// 1. Pick Random Genre
// -----------------------------------------
async function pickRandomGenreUsingAI() {
	
    const genres = [
  "Alternative Dance",
  "Alternative Pop",
  "Ambient",
  "Anti-Pop",
  "Bass",
  "Bass House",
  "Bass Music",
  "Brazilian Phonk",
  "Breakbeat",
  "Chill",
  "Chill Bass",
  "Chill Pop",
  "Colour Bass",
  "Complextro",
  "Dance-Pop",
  "Deep House",
  "Disco",
  "Disco House",
  "Drum & Bass",
  "Drumstep",
  "Dubstep",
  "EDM",
  "Electro",
  "Electro House",
  "Electronic",
  "Electronic Pop",
  "Electronic Rock",
  "Future Bass",
  "Future Bounce",
  "Future Funk",
  "Future House",
  "Future Rave",
  "Future Trap",
  "Futurepop",
  "Garage",
  "Glitch Hop",
  "Hardcore",
  "Hardstyle",
  "House",
  "Hyperpop",
  "Indie Dance",
  "J-Pop",
  "Jersey Club",
  "Jump-Up",
  "Liquid DnB",
  "Lofi Hip-Hop",
  "Melodic Dubstep",
  "Melodic House",
  "Midtempo Bass",
  "Neurofunk",
  "Nu-Jazz",
  "Phonk",
  "Pluggnb",
  "Pop",
  "Progressive House",
  "RnB",
  "Speed Garage",
  "Tech House",
  "Techno",
  "Trance",
  "Trap",
  "Tribal House",
  "UKG",
  "Wave",
  "Witch House"
];

    const prompt = `
Choose a RANDOM genre from this list:
${genres[Math.random()]}

Rules:
- Suitable for calm, educational background music.
- Must be instrumental-compatible.
- Must return exactly one avaible genre in page:

Randomizer: ${Math.random()}
    `;

    const genre = await rateLimitedGeminiCall(prompt);

    return genres.includes(genre) ? genre : null;
}

// -----------------------------------------
// 2. Pick Random Page
// -----------------------------------------
async function pickRandomPageUsingAI(maxPages = 40) {
    const prompt = `
Pick a random page number between 0 and ${maxPages}.
Only return the number.
Randomizer: ${Math.random()}
    `;

    const num = parseInt(await rateLimitedGeminiCall(prompt), 10);
    return !isNaN(num) ? num : Math.floor(Math.random() * maxPages);
}

// -----------------------------------------
// NCS Helpers
// -----------------------------------------
async function searchInstrumentalByGenre(genre, page) {
    return await ncs.search(
        { genre: ncs.Genre[genre], instrumentalOnly: true },
        page
    );
}

function pickRandomSong(songs) {
    if (!songs || songs.length === 0) return null;
    return songs[Math.floor(Math.random() * songs.length)];
}

async function downloadInstrumental(song) {
    const url = song.download?.instrumental;
    if (!url) return false;

    console.log(`⬇️ Downloading: ${song.name}`);

    const { data } = await axios.get(url, { responseType: "arraybuffer" });
    const filename = `${defaultDirectory}${song.name}-instrumental.mp3`;

    await fs.writeFile(filename, data);
    console.log(`✅ Download complete: ${filename}`);

    return true;
}

// -----------------------------------------
// MAIN LOOP: Retries until success
// Rate limited, safe for free tier
// -----------------------------------------
async function main() {
    let attempts = 0;
    const MAX_ATTEMPTS = 50;

    while (attempts < MAX_ATTEMPTS) {
        attempts++;

        console.log(`\n🔁 Attempt #${attempts}`);

        console.log("🤖 Asking Gemini for a random genre...");
        const genre = await pickRandomGenreUsingAI();

        if (!genre) {
            console.log("⚠️ Invalid genre, trying again...");
            continue;
        }

        console.log("🎵 Chosen Genre:", genre);

        console.log("🤖 Asking Gemini for a random page...");
        const page = await pickRandomPageUsingAI();
        console.log("📄 Chosen Page:", page);

        console.log(`🎼 Searching genre: ${genre}, page: ${page}...`);
        const results = await searchInstrumentalByGenre(genre, page);

        if (!results?.length) {
            console.log("❌ Empty result set. Trying new genre/page...");
            continue;
        }

        const song = pickRandomSong(results);

        if (!song) {
            console.log("❌ No random song selected. Retrying...");
            continue;
        }

        console.log(`🎵 Selected Song: ${song.name}`);

        const success = await downloadInstrumental(song);
        if (success) return; // SUCCESS!

        console.log("❌ No instrumental download for this song. Retrying...");
    }

    console.log("❌ Max attempts reached. No downloadable song found.");
}

main();

