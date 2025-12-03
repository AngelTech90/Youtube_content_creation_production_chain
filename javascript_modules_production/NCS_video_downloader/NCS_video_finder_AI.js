import ncs from "nocopyrightsounds-api";
import axios from "axios";
import fs from "fs/promises";
import dotenv from "dotenv";
import path from "path";
import { GoogleGenerativeAI } from "@google/generative-ai";

dotenv.config();

const defaultDirectory = '../../in_production_content/downloaded_music/';
const transcriptionDirectory = '../../in_production_content/transcriptions/';

// Gemini setup
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({
    model: "gemini-2.0-flash-exp",
    generationConfig: {
        temperature: 0.8,  // Slightly lower for more focused results
        topK: 40,
        topP: 0.95
    }
});

// -----------------------------------------
// RATE LIMITING: 1 request every 4 seconds
// -----------------------------------------
let lastRequestTime = 0;
const REQUEST_DELAY = 4000;

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
            if (err.status === 429) {
                attempts++;
                const backoff = Math.min(8000 * attempts, 30000);
                console.log(`⚠️ Gemini rate limit hit. Waiting ${backoff}ms before retry...`);
                await new Promise(res => setTimeout(res, backoff));
                continue;
            }
            throw err;
        }
    }
}

// -----------------------------------------
// GENRE FILTERING
// -----------------------------------------
const EXCLUDED_GENRES = [
    "Dubstep", "Melodic Dubstep", "Drumstep",
    "Hardcore", "Hardstyle", 
    "Brazilian Phonk", "Phonk",
    "Future Funk", "Funk",
    "Trap", "Future Trap",
    "Jump-Up", "Neurofunk",
    "Bass House", "Midtempo Bass",
    "Glitch Hop", "Breakbeat",
    "Complextro", "Electro"
];

const PREFERRED_GENRES = [
    "Lofi Hip-Hop", "Ambient", "Chill", "Chill Pop", "Chill Bass",
    "Nu-Jazz", "Melodic House", "Deep House", "Progressive House",
    "Future Bass", "Electronic Pop", "Alternative Pop",
    "Indie Dance", "Wave"
];

function isGenreAllowed(genre) {
    return !EXCLUDED_GENRES.includes(genre);
}

// -----------------------------------------
// LOAD TRANSCRIPTION
// -----------------------------------------
async function loadTranscription() {
    try {
        const files = await fs.readdir(transcriptionDirectory);
        const txtFiles = files.filter(f => f.endsWith('.txt'));
        
        if (txtFiles.length === 0) {
            console.log("⚠️ No transcription files found. Using random selection.");
            return null;
        }
        
        const transcriptionFile = path.join(transcriptionDirectory, txtFiles[0]);
        const content = await fs.readFile(transcriptionFile, 'utf-8');
        
        console.log(`📄 Loaded transcription: ${txtFiles[0]} (${content.length} chars)`);
        return content;
    } catch (err) {
        console.log(`⚠️ Error loading transcription: ${err.message}`);
        return null;
    }
}

// -----------------------------------------
// ANALYZE TRANSCRIPTION FOR MUSIC GENRE
// -----------------------------------------
async function analyzeVideoForGenre(transcription) {
    const genres = [
        "Alternative Dance", "Alternative Pop", "Ambient", "Anti-Pop", "Bass",
        "Bass House", "Bass Music", "Brazilian Phonk", "Breakbeat", "Chill",
        "Chill Bass", "Chill Pop", "Colour Bass", "Complextro", "Dance-Pop",
        "Deep House", "Disco", "Disco House", "Drum & Bass", "Drumstep",
        "Dubstep", "EDM", "Electro", "Electro House", "Electronic",
        "Electronic Pop", "Electronic Rock", "Future Bass", "Future Bounce",
        "Future Funk", "Future House", "Future Rave", "Future Trap",
        "Futurepop", "Garage", "Glitch Hop", "Hardcore", "Hardstyle",
        "House", "Hyperpop", "Indie Dance", "J-Pop", "Jersey Club",
        "Jump-Up", "Liquid DnB", "Lofi Hip-Hop", "Melodic Dubstep",
        "Melodic House", "Midtempo Bass", "Neurofunk", "Nu-Jazz", "Phonk",
        "Pluggnb", "Pop", "Progressive House", "RnB", "Speed Garage",
        "Tech House", "Techno", "Trance", "Trap", "Tribal House",
        "UKG", "Wave", "Witch House"
    ];

    const prompt = `You are a music supervisor for video content. Analyze this video transcription and recommend the BEST background music genre.

VIDEO TRANSCRIPTION:
${transcription.slice(0, 2000)}${transcription.length > 2000 ? '...' : ''}

AVAILABLE GENRES:
${genres.join(", ")}

ANALYSIS CRITERIA:
1. **Video Tone**: Is it motivational, educational, calm, intense, emotional?
2. **Content Type**: Tutorial, vlog, presentation, storytelling, documentary?
3. **Pacing**: Fast-paced or slow-paced content?
4. **Target Audience**: Professional, casual, young, broad?

SELECTION RULES:
- Choose genres that COMPLEMENT the content without overwhelming it
- Educational/Tutorial content → Lofi Hip-Hop, Chill, Ambient, Nu-Jazz
- Motivational content → Future Bass, Electronic Pop, Progressive House
- Storytelling → Ambient, Chill, Melodic House
- High-energy content → EDM, Electro House, Trap
- Professional/Business → Deep House, Chill, Ambient

Return ONLY the genre name from the list above. No explanation, just the genre name.

Example responses:
- "Lofi Hip-Hop"
- "Ambient"
- "Future Bass"

Your recommendation:`;

    const genre = await rateLimitedGeminiCall(prompt);
    const cleanGenre = genre.replace(/['"]/g, '').trim();
    
    // Validate it's in the list
    if (genres.includes(cleanGenre)) {
        return cleanGenre;
    }
    
    // Fuzzy match
    const fuzzyMatch = genres.find(g => 
        g.toLowerCase() === cleanGenre.toLowerCase() ||
        cleanGenre.toLowerCase().includes(g.toLowerCase()) ||
        g.toLowerCase().includes(cleanGenre.toLowerCase())
    );
    
    return fuzzyMatch || null;
}

// -----------------------------------------
// PICK TOP 5 GENRE OPTIONS FOR VIDEO
// -----------------------------------------
async function pickGenreOptionsForVideo(transcription) {
    const allGenres = [
        "Alternative Dance", "Alternative Pop", "Ambient", "Anti-Pop",
        "Chill", "Chill Bass", "Chill Pop",
        "Deep House", "Disco House",
        "Electronic", "Electronic Pop",
        "Future Bass", "Future House",
        "House", "Indie Dance", "J-Pop",
        "Liquid DnB", "Lofi Hip-Hop",
        "Melodic House", "Nu-Jazz",
        "Pop", "Progressive House", "RnB",
        "Tech House", "Wave"
    ];

    const prompt = `Analyze this video transcription and suggest the TOP 5 most suitable CALM, SIMPLE, INSTRUMENTAL background music genres.

VIDEO TRANSCRIPTION:
${transcription.slice(0, 2000)}${transcription.length > 2000 ? '...' : ''}

AVAILABLE GENRES (only choose from these):
${allGenres.join(", ")}

STRICT REQUIREMENTS:
✅ PRIORITIZE: Lofi Hip-Hop, Ambient, Chill, Nu-Jazz, Deep House, Progressive House, Future Bass
✅ Simple, clean, non-aggressive instrumental music
✅ Suitable for background listening (won't distract from narration)
✅ Professional, calm, focused atmosphere

❌ AVOID: Dubstep, Trap, Phonk, Hardcore, Bass-heavy, Aggressive genres
❌ No funk, no heavy bass, no aggressive beats

SELECTION CRITERIA:
- Educational/Tutorial content → Lofi Hip-Hop, Ambient, Chill, Nu-Jazz
- Motivational content → Future Bass, Electronic Pop, Progressive House, Chill
- Storytelling → Ambient, Melodic House, Wave, Chill
- Professional content → Deep House, Ambient, Lofi Hip-Hop, Nu-Jazz

Return EXACTLY 5 genre names as a JSON array, ordered by suitability (best first).
Use ONLY genres from the list above.

Format: ["Genre1", "Genre2", "Genre3", "Genre4", "Genre5"]

Example: ["Lofi Hip-Hop", "Ambient", "Chill", "Nu-Jazz", "Future Bass"]

Your response (JSON array only):`;

    const response = await rateLimitedGeminiCall(prompt);
    
    try {
        // Extract JSON array
        const jsonMatch = response.match(/\[(.*?)\]/s);
        if (!jsonMatch) {
            throw new Error("No JSON array found");
        }
        
        const parsed = JSON.parse(jsonMatch[0]);
        
        // Validate, filter excluded genres, and limit to allowed genres
        const validGenres = parsed
            .map(g => g.replace(/['"]/g, '').trim())
            .filter(g => allGenres.includes(g) && isGenreAllowed(g))
            .slice(0, 5);
        
        // If we got less than 5, add preferred genres as fallback
        while (validGenres.length < 5) {
            const fallback = PREFERRED_GENRES.find(g => 
                !validGenres.includes(g) && allGenres.includes(g)
            );
            if (fallback) {
                validGenres.push(fallback);
            } else {
                break;
            }
        }
        
        return validGenres.length > 0 ? validGenres : null;
        
    } catch (err) {
        console.log(`⚠️ Failed to parse genre suggestions: ${err.message}`);
        return null;
    }
}

// -----------------------------------------
// PICK RANDOM PAGE
// -----------------------------------------
async function pickRandomPage(maxPages = 10) {
    // Prefer earlier pages (more popular songs)
    const page = Math.floor(Math.random() * Math.min(maxPages, 10));
    return page;
}

// -----------------------------------------
// NCS HELPERS
// -----------------------------------------
async function searchInstrumentalByGenre(genre, page) {
    try {
        const results = await ncs.search(
            { 
                genre: ncs.Genre[genre], 
                instrumentalOnly: true 
            },
            page
        );
        return results;
    } catch (err) {
        console.log(`   ⚠️ Search error for ${genre}: ${err.message}`);
        return [];
    }
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
// MAIN LOOP WITH SMART GENRE SELECTION
// -----------------------------------------
async function main() {
    console.log("🎵 SMART MUSIC DOWNLOADER");
    console.log("=" .repeat(70));
    
    // Load transcription
    console.log("\n📄 Loading video transcription...");
    const transcription = await loadTranscription();
    
    let genreOptions = [];
    
    if (transcription) {
        console.log("\n🤖 Analyzing video content with Gemini AI...");
        genreOptions = await pickGenreOptionsForVideo(transcription);
        
        if (genreOptions) {
            console.log(`✅ Recommended genres (in order):`);
            genreOptions.forEach((g, i) => console.log(`   ${i + 1}. ${g}`));
        } else {
            console.log("⚠️ Could not analyze transcription, using random selection");
        }
    }
    
    // If no transcription or analysis failed, use preferred genres
    if (!genreOptions || genreOptions.length === 0) {
        console.log("⚠️ Using default preferred genres");
        genreOptions = PREFERRED_GENRES.slice(0, 5);
    }
    
    console.log(`\n🎼 Will search in ${genreOptions.length} genres`);
    console.log(`🚫 Excluded genres: ${EXCLUDED_GENRES.slice(0, 5).join(", ")}...`);
    
    // Try each genre option
    let attempts = 0;
    const MAX_ATTEMPTS = 45;
    
    for (const genre of genreOptions) {
        console.log(`\n🎼 Searching genre: ${genre}`);
        
        let genreAttempts = 0;
        const MAX_GENRE_ATTEMPTS = 7;
        
        while (genreAttempts < MAX_GENRE_ATTEMPTS && attempts < MAX_ATTEMPTS) {
            genreAttempts++;
            attempts++;
            
            const page = pickRandomPage();
            console.log(`   📄 Page ${page}, Attempt ${genreAttempts}/${MAX_GENRE_ATTEMPTS}`);
            
            try {
                const results = await searchInstrumentalByGenre(genre, page);
                
                if (!results?.length) {
                    console.log("   ❌ Empty result set");
                    continue;
                }
                
                const song = pickRandomSong(results);
                
                if (!song) {
                    console.log("   ❌ No song selected");
                    continue;
                }
                
                console.log(`   🎵 Selected: ${song.name}`);
                
                const success = await downloadInstrumental(song);
                if (success) {
                    console.log("\n" + "=".repeat(70));
                    console.log("✅ SUCCESS! Music downloaded and ready to use!");
                    console.log("=".repeat(70));
                    return;
                }
                
                console.log("   ❌ No instrumental download available");
                
            } catch (err) {
                console.log(`   ⚠️ Error: ${err.message}`);
            }
        }
    }
    
    console.log("\n❌ Max attempts reached. No downloadable song found.");
    console.log("💡 Try running again or check your transcription file.");
}

main().catch(console.error);
