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
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="orchestrator_${TIMESTAMP}.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Module directories - Based on actual structure
NCS_DOWNLOADER="../javascript_modules_production/NCS_video_downloader/"
VIDEO_SEPARATOR="./Video_and_audio_separator"
TIMESTAMPS_EXTRACTOR="./Video_timestamps_extractor"
AUDIO_ENHANCER="./CleanvoiceAI_audio_enhancer"
PEXELS_DOWNLOADER="./Pexels_videos_downloader"
VIDEO_INDEXER="./Video_clips_indexer"
SUBTITLES_INDEXER="./Videos_subtitles_indexer"
TITLES_GENERATOR="./Video_titles_generator"
DESCRIPTIONS_GENERATOR="./Videos_descriptions_generator"
HASHTAGS_GENERATOR="./Videos_hashtags_generator"
VIDEO_ENHANCER="./FFMPEG_video_enhancer"
AUDIO_MIXER="./Video_and_audio_mixer"
MUSIC_INDEXER="./Video_music_indexer"
SHORTS_EXTRACTOR="./Youtube_shorts_video_extractor"
UPLOADER="./Youtube_uploader"

# Array to store processes to skip
declare -a SKIP_PROCESSES=()

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

print_info() {
    echo -e "${BLUE}[$(date +%H:%M:%S)] INFO: $1${NC}"
    echo "[$(date +%H:%M:%S)] INFO: $1" >> "$LOG_FILE"
}

check_module_exists() {
    local module_dir=$1
    
    if [ ! -d "$module_dir" ]; then
        return 1
    fi
    return 0
}

should_skip_process() {
    local process_num=$1
    for skip in "${SKIP_PROCESSES[@]}"; do
        if [ "$skip" -eq "$process_num" ]; then
            return 0  # Should skip
        fi
    done
    return 1  # Should not skip
}

run_module() {
    local module_name=$1
    local module_dir=$2
    local is_critical=$3  # true or false
    
    print_step "Running: $module_name"
    print_info "Module path: $module_dir"
    
    if ! check_module_exists "$module_dir"; then
        print_warning "Directory not found: $module_dir"
        if [ "$is_critical" = "true" ]; then
            print_error "Critical module missing!"
            return 1
        else
            print_warning "Skipping non-critical module..."
            return 0
        fi
    fi
    
    if [ ! -f "$module_dir/script_runner.sh" ]; then
        print_warning "script_runner.sh not found in: $module_dir"
        print_info "Looking for Python scripts in module..."
        
        local python_scripts=$(find "$module_dir" -maxdepth 1 -name "*.py" -type f)
        if [ -z "$python_scripts" ]; then
            if [ "$is_critical" = "true" ]; then
                print_error "No scripts found in module"
                return 1
            else
                print_warning "No scripts found, skipping..."
                return 0
            fi
        fi
    fi
    
    cd "$module_dir" || return 1
    
    if [ -f "script_runner.sh" ]; then
        bash script_runner.sh >> "../../$LOG_FILE" 2>&1
    else
        # Try to run main Python script directly
        local main_script=$(ls *.py 2>/dev/null | head -1)
        if [ -n "$main_script" ]; then
            python3 "$main_script" >> "../../$LOG_FILE" 2>&1
        fi
    fi
    
    local status=$?
    cd - > /dev/null || return 1
    
    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✓ $module_name completed${NC}"
        echo "[$(date +%H:%M:%S)] ✓ $module_name completed" >> "$LOG_FILE"
        return 0
    else
        print_error "$module_name failed with status $status"
        if [ "$is_critical" = "true" ]; then
            return 1
        else
            print_warning "Continuing despite failure..."
            return 0
        fi
    fi
}

run_javascript_module() {
    local module_name=$1
    local module_dir=$2
    local is_critical=$3

    print_step "Running: $module_name"
    print_info "Module directory: $module_dir"

    if ! check_module_exists "$module_dir"; then
        print_warning "Directory not found: $module_dir"
        if [ "$is_critical" = "true" ]; then
            print_error "Critical module missing!"
            return 1
        else
            print_warning "Skipping non-critical module..."
            return 0
        fi
    fi

    # Check if Node.js exists
    if ! command -v node &> /dev/null; then
        print_warning "Node.js not installed, skipping JavaScript module"
        return 0
    fi

    cd "$module_dir" || return 1

    if [ -f "script_runner.sh" ]; then
        print_info "Found script_runner.sh — running it..."
        bash script_runner.sh >> "../../$LOG_FILE" 2>&1
    else
        print_warning "No script_runner.sh found, executing all .js files directly..."

        local js_scripts=$(find . -maxdepth 1 -name "*.js" -type f)
        if [ -z "$js_scripts" ]; then
            print_warning "No JavaScript files found in: $module_dir"
            cd - > /dev/null || return 1
            return 0
        fi

        for script in $js_scripts; do
            print_info "Running $script ..."
            node "$script" >> "../../$LOG_FILE" 2>&1
            local status=$?
            if [ $status -ne 0 ]; then
                print_error "Script $script failed with status $status"
                if [ "$is_critical" = "true" ]; then
                    cd - > /dev/null || return 1
                    return 1
                else
                    print_warning "Continuing despite failure..."
                fi
            fi
        done
    fi

    local status=$?
    cd - > /dev/null || return 1

    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✓ $module_name completed${NC}"
        echo "[$(date +%H:%M:%S)] ✓ $module_name completed" >> "$LOG_FILE"
        return 0
    else
        print_error "$module_name failed with status $status"
        if [ "$is_critical" = "true" ]; then
            return 1
        else
            print_warning "Continuing despite failure..."
            return 0
        fi
    fi
}

# ============================================================
# Process Selection Menu
# ============================================================

show_process_menu() {
    echo -e "\n${CYAN}=====================================================${NC}"
    echo -e "${CYAN}  AVAILABLE PIPELINE PROCESSES${NC}"
    echo -e "${CYAN}=====================================================${NC}\n"
    
    echo -e "${YELLOW}Select processes to SKIP (enter numbers separated by space)${NC}"
    echo -e "${YELLOW}Press ENTER to run all processes${NC}\n"
    
    echo "  1.  Audio Separation"
    echo "  2.  Timestamp Extraction"
    echo "  3.  NCS Music Download"
    echo "  4.  Audio Enhancement"
    echo "  5.  Pexels Video Download"
    echo "  6.  Video Clip Indexing"
    echo "  7.  Subtitles Indexing"
    echo "  8.  Title Generation"
    echo "  9.  Description Generation"
    echo "  10. Hashtags Generation"
    echo "  11. Video Enhancement"
    echo "  12. Audio-Video Mixing"
    echo "  13. Music Indexing"
    echo "  14. YouTube Shorts Extraction"
    echo "  15. YouTube Upload"
    
    echo -e "\n${CYAN}=====================================================${NC}"
    echo -n "Enter process numbers to skip (e.g., 3 5 12): "
    
    read -r skip_input
    
    if [ -n "$skip_input" ]; then
        SKIP_PROCESSES=($skip_input)
        echo -e "\n${YELLOW}Will skip processes: ${SKIP_PROCESSES[*]}${NC}\n"
    else
        echo -e "\n${GREEN}Running all processes${NC}\n"
    fi
    
    sleep 2
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
    echo "Script directory: $SCRIPT_DIR"
    echo "Pipeline started at $(date)" > "$LOG_FILE"
    echo "Script directory: $SCRIPT_DIR" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    
    # Show process selection menu
    show_process_menu
    
    # Step 1: Separate Video and Audio
    if ! should_skip_process 1; then
        echo -e "\n${BLUE}[STEP 1/15] Audio Separation${NC}"
        if ! run_module "Video and Audio Separator" "$VIDEO_SEPARATOR" "false"; then
            print_warning "Audio separation skipped"
        fi
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 1/15] Audio Separation - SKIPPED${NC}\n"
    fi
    
    # Step 2: Extract Timestamps
    if ! should_skip_process 2; then
        echo -e "\n${BLUE}[STEP 2/15] Timestamp Extraction${NC}"
        if ! run_module "Video Timestamps Extractor" "$TIMESTAMPS_EXTRACTOR" "false"; then
            print_warning "Timestamp extraction skipped"
        fi
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 2/15] Timestamp Extraction - SKIPPED${NC}\n"
    fi
    
    # Step 3: Download NCS Music
    if ! should_skip_process 3; then
        echo -e "\n${BLUE}[STEP 3/15] Music Download${NC}"
        if [ -f "$NCS_DOWNLOADER/NCS_video_finder_AI.js" ]; then
            run_javascript_module "NCS Video Downloader" "$NCS_DOWNLOADER" "false" || true
        else
            print_warning "NCS downloader not found, skipping..."
        fi
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 3/15] Music Download - SKIPPED${NC}\n"
    fi
    
    # Step 4: Enhance Audio
    if ! should_skip_process 4; then
        echo -e "\n${BLUE}[STEP 4/15] Audio Enhancement${NC}"
        run_module "CleanvoiceAI Audio Enhancer" "$AUDIO_ENHANCER" "false" || true
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 4/15] Audio Enhancement - SKIPPED${NC}\n"
    fi
    
    # Step 5: Download Complementary Videos
    if ! should_skip_process 5; then
        echo -e "\n${BLUE}[STEP 5/15] Pexels Video Download${NC}"
        run_module "Pexels Videos Downloader" "$PEXELS_DOWNLOADER" "false" || true
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 5/15] Pexels Video Download - SKIPPED${NC}\n"
    fi
    
    # Step 6: Index Video Clips
    if ! should_skip_process 6; then
        echo -e "\n${BLUE}[STEP 6/15] Video Clip Indexing${NC}"
        run_module "Video Clips Indexer" "$VIDEO_INDEXER" "false" || true
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 6/15] Video Clip Indexing - SKIPPED${NC}\n"
    fi
    
    # Step 7: Index Subtitles
    if ! should_skip_process 7; then
        echo -e "\n${BLUE}[STEP 7/15] Subtitles Indexing${NC}"
        run_module "Video Subtitles Indexer" "$SUBTITLES_INDEXER" "false" || true
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 7/15] Subtitles Indexing - SKIPPED${NC}\n"
    fi
    
    # Step 8: Generate Titles
    if ! should_skip_process 8; then
        echo -e "\n${BLUE}[STEP 8/15] Title Generation${NC}"
        run_module "Video Titles Generator" "$TITLES_GENERATOR" "false" || true
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 8/15] Title Generation - SKIPPED${NC}\n"
    fi
    
    # Step 9: Generate Descriptions
    if ! should_skip_process 9; then
        echo -e "\n${BLUE}[STEP 9/15] Description Generation${NC}"
        run_module "Videos Descriptions Generator" "$DESCRIPTIONS_GENERATOR" "false" || true
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 9/15] Description Generation - SKIPPED${NC}\n"
    fi
    
    # Step 10: Generate Hashtags
    if ! should_skip_process 10; then
        echo -e "\n${BLUE}[STEP 10/15] Hashtags Generation${NC}"
        run_module "Videos Hashtags Generator" "$HASHTAGS_GENERATOR" "false" || true
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 10/15] Hashtags Generation - SKIPPED${NC}\n"
    fi
    
    # Step 11: Enhance Video
    if ! should_skip_process 11; then
        echo -e "\n${BLUE}[STEP 11/15] Video Enhancement${NC}"
        run_module "Video Enhancer" "$VIDEO_ENHANCER" "false" || true
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 11/15] Video Enhancement - SKIPPED${NC}\n"
    fi
    
    # Step 12: Mix Audio and Video
    if ! should_skip_process 12; then
        echo -e "\n${BLUE}[STEP 12/15] Audio-Video Mixing${NC}"
        run_module "Video and Audio Mixer" "$AUDIO_MIXER" "false" || true
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 12/15] Audio-Video Mixing - SKIPPED${NC}\n"
    fi
    
    # Step 13: Music Indexing
    if ! should_skip_process 13; then
        echo -e "\n${BLUE}[STEP 13/15] Music Indexing${NC}"
        run_module "Video Music Indexer" "$MUSIC_INDEXER" "false" || true
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 13/15] Music Indexing - SKIPPED${NC}\n"
    fi
    
    # Step 14: Extract Shorts
    if ! should_skip_process 14; then
        echo -e "\n${BLUE}[STEP 14/15] YouTube Shorts Extraction${NC}"
        run_module "YouTube Shorts Video Extractor" "$SHORTS_EXTRACTOR" "false" || true
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 14/15] YouTube Shorts Extraction - SKIPPED${NC}\n"
    fi
    
    # Step 15: Upload to YouTube
    if ! should_skip_process 15; then
        echo -e "\n${BLUE}[STEP 15/15] YouTube Upload${NC}"
        run_module "YouTube Uploader" "$UPLOADER" "false" || true
        echo ""
    else
        echo -e "\n${YELLOW}[STEP 15/15] YouTube Upload - SKIPPED${NC}\n"
    fi
    
    return 0
}

# ============================================================
# Execution
# ============================================================

if main; then
    echo -e "\n${GREEN}=====================================================${NC}"
    echo -e "${GREEN}  ✓ Pipeline completed!${NC}"
    echo -e "${GREEN}  Finished: $(date)${NC}"
    echo -e "${GREEN}=====================================================${NC}"
    echo ""
    echo "Check $LOG_FILE for detailed logs"
    exit 0
else
    echo -e "\n${RED}=====================================================${NC}"
    echo -e "${RED}  ✗ Pipeline encountered issues${NC}"
    echo -e "${RED}  Finished: $(date)${NC}"
    echo -e "${RED}=====================================================${NC}"
    echo ""
    echo "Check $LOG_FILE for error details"
    exit 1
fi
