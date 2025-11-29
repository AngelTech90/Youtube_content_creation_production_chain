#!/bin/bash

# ============================================================
# Master Pipeline Orchestrator
# Automates the full YouTube Shorts production workflow
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="orchestrator_${TIMESTAMP}.log"

# Module directories
NCS_DOWNLOADER="../javascript_production_modules/NCS_video_downloader"
VIDEO_SEPARATOR="Video_and_audio_separator"
TIMESTAMPS_EXTRACTOR="Video_timestamps_extractor"
AUDIO_ENHANCER="CleanvoiceAI_audio_enhancer"
PEXELS_DOWNLOADER="Pexels_videos_downloader"
VIDEO_INDEXER="Video_clips_indexer"
SUBTITLES_INDEXER="Video_subtitles_indexer"
TITLES_GENERATOR="Video_titles_generator"
DESCRIPTIONS_GENERATOR="Videos_descriptions_generator"
HASHTAGS_GENERATOR="Videos_hashtags_generator"
AUDIO_MIXER="Video_and_audio_mixer"
MUSIC_INDEXER="Video_music_indexer"
SHORTS_EXTRACTOR="Youtube_shorts_video_extractor"
UPLOADER="Youtube_uploader"

# ============================================================
# Helper Functions
# ============================================================

print_step() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} ${GREEN}$1${NC}"
    echo "[$(date +%H:%M:%S)] $1" >> "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[$(date +%H:%M:%S)] ERROR: $1${NC}"
    echo "[$(date +%H:%M:%S)] ERROR: $1" >> "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[$(date +%H:%M:%S)] WARNING: $1${NC}"
    echo "[$(date +%H:%M:%S)] WARNING: $1" >> "$LOG_FILE"
}

run_module() {
    local module_name=$1
    local module_dir=$2
    
    print_step "Running: $module_name"
    
    if [ ! -d "$module_dir" ]; then
        print_error "Directory not found: $module_dir"
        return 1
    fi
    
    if [ ! -f "$module_dir/script_runner.sh" ]; then
        print_error "script_runner.sh not found in: $module_dir"
        return 1
    fi
    
    cd "$module_dir"
    bash script_runner.sh >> "../../$LOG_FILE" 2>&1
    local status=$?
    cd - > /dev/null
    
    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✓ $module_name completed${NC}"
        echo "[$(date +%H:%M:%S)] ✓ $module_name completed" >> "$LOG_FILE"
        return 0
    else
        print_error "$module_name failed with status $status"
        return 1
    fi
}

run_javascript_module() {
    local module_name=$1
    local script_path=$2
    
    print_step "Running: $module_name"
    
    if [ ! -f "$script_path" ]; then
        print_error "Script not found: $script_path"
        return 1
    fi
    
    node "$script_path" >> "$LOG_FILE" 2>&1
    local status=$?
    
    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✓ $module_name completed${NC}"
        echo "[$(date +%H:%M:%S)] ✓ $module_name completed" >> "$LOG_FILE"
        return 0
    else
        print_error "$module_name failed with status $status"
        return 1
    fi
}

# ============================================================
# Main Pipeline
# ============================================================

main() {
    echo -e "${BLUE}=====================================================${NC}"
    echo -e "${BLUE}  YouTube Shorts Production Pipeline${NC}"
    echo -e "${BLUE}  Started: $(date)${NC}"
    echo -e "${BLUE}=====================================================${NC}"
    echo ""
    
    echo "Logging to: $LOG_FILE"
    echo "Pipeline started at $(date)" > "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    
    # Step 1: Download NCS Music
    echo -e "\n${BLUE}[STEP 1/14] Music Download${NC}"
    if run_javascript_module "NCS Video Downloader" "$NCS_DOWNLOADER/NCS_video_finder_AI.js"; then
        echo ""
    else
        print_warning "Continuing despite NCS downloader issue..."
    fi
    
    # Step 2: Separate Video and Audio
    echo -e "\n${BLUE}[STEP 2/14] Audio Separation${NC}"
    if ! run_module "Video and Audio Separator" "$VIDEO_SEPARATOR"; then
        print_error "Pipeline halted at step 2"
        return 1
    fi
    echo ""
    
    # Step 3: Extract Timestamps
    echo -e "\n${BLUE}[STEP 3/14] Timestamp Extraction${NC}"
    if ! run_module "Video Timestamps Extractor" "$TIMESTAMPS_EXTRACTOR"; then
        print_error "Pipeline halted at step 3"
        return 1
    fi
    echo ""
    
    # Step 4: Enhance Audio
    echo -e "\n${BLUE}[STEP 4/14] Audio Enhancement${NC}"
    if ! run_module "CleanvoiceAI Audio Enhancer" "$AUDIO_ENHANCER"; then
        print_warning "Audio enhancement failed, continuing..."
    fi
    echo ""
    
    # Step 5: Download Complementary Videos
    echo -e "\n${BLUE}[STEP 5/14] Pexels Video Download${NC}"
    if ! run_module "Pexels Videos Downloader" "$PEXELS_DOWNLOADER"; then
        print_warning "Pexels download failed, continuing..."
    fi
    echo ""
    
    # Step 6: Index Video Clips
    echo -e "\n${BLUE}[STEP 6/14] Video Clip Indexing${NC}"
    if ! run_module "Video Clips Indexer" "$VIDEO_INDEXER"; then
        print_warning "Video indexing failed, continuing..."
    fi
    echo ""
    
    # Step 7: Index Subtitles
    echo -e "\n${BLUE}[STEP 7/14] Subtitles Indexing${NC}"
    if ! run_module "Video Subtitles Indexer" "$SUBTITLES_INDEXER"; then
        print_warning "Subtitles indexing failed, continuing..."
    fi
    echo ""
    
    # Step 8: Generate Titles
    echo -e "\n${BLUE}[STEP 8/14] Title Generation${NC}"
    if ! run_module "Video Titles Generator" "$TITLES_GENERATOR"; then
        print_warning "Title generation failed, continuing..."
    fi
    echo ""
    
    # Step 9: Generate Descriptions
    echo -e "\n${BLUE}[STEP 9/14] Description Generation${NC}"
    if ! run_module "Videos Descriptions Generator" "$DESCRIPTIONS_GENERATOR"; then
        print_warning "Description generation failed, continuing..."
    fi
    echo ""
    
    # Step 10: Generate Hashtags
    echo -e "\n${BLUE}[STEP 10/14] Hashtags Generation${NC}"
    if ! run_module "Videos Hashtags Generator" "$HASHTAGS_GENERATOR"; then
        print_warning "Hashtags generation failed, continuing..."
    fi
    echo ""
    
    # Step 11: Mix Audio and Video
    echo -e "\n${BLUE}[STEP 11/14] Audio-Video Mixing${NC}"
    if ! run_module "Video and Audio Mixer" "$AUDIO_MIXER"; then
        print_warning "Audio-video mixing failed, continuing..."
    fi
    echo ""
    
    # Step 12: Music Indexing
    echo -e "\n${BLUE}[STEP 12/14] Music Indexing${NC}"
    if ! run_module "Video Music Indexer" "$MUSIC_INDEXER"; then
        print_warning "Music indexing failed, continuing..."
    fi
    echo ""
    
    # Step 13: Extract Shorts
    echo -e "\n${BLUE}[STEP 13/14] YouTube Shorts Extraction${NC}"
    if ! run_module "YouTube Shorts Video Extractor" "$SHORTS_EXTRACTOR"; then
        print_error "Pipeline halted at step 13"
        return 1
    fi
    echo ""
    
    # Step 14: Upload to YouTube
    echo -e "\n${BLUE}[STEP 14/14] YouTube Upload${NC}"
    if ! run_module "YouTube Uploader" "$UPLOADER"; then
        print_warning "YouTube upload failed, but clips are ready"
    fi
    echo ""
    
    return 0
}

# ============================================================
# Execution
# ============================================================

if main; then
    echo -e "\n${GREEN}=====================================================${NC}"
    echo -e "${GREEN}  ✓ Pipeline completed successfully!${NC}"
    echo -e "${GREEN}  Finished: $(date)${NC}"
    echo -e "${GREEN}=====================================================${NC}"
    echo ""
    echo "Check $LOG_FILE for detailed logs"
    exit 0
else
    echo -e "\n${RED}=====================================================${NC}"
    echo -e "${RED}  ✗ Pipeline failed!${NC}"
    echo -e "${RED}  Finished: $(date)${NC}"
    echo -e "${RED}=====================================================${NC}"
    echo ""
    echo "Check $LOG_FILE for error details"
    exit 1
fi
