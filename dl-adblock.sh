#!/bin/bash

# Change to the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || { echo "Failed to change to script directory"; exit 1; }

# Initialize variables
SILENT=false
LOG_FILE="$SCRIPT_DIR/dl-adblock.log"

# Process command line arguments
for arg in "$@"; do
  case $arg in
    --silent)
      SILENT=true
      shift
      ;;
    *)
      # Unknown option
      echo "Unknown option: $arg"
      echo "Usage: $0 [--silent]"
      exit 1
      ;;
  esac
done

# Function to log messages
log() {
  local message="$1"
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

  if [ "$SILENT" = true ]; then
    echo "[$timestamp] $message" >> "$LOG_FILE"
  else
    echo "[$timestamp] $message" | tee -a "$LOG_FILE"
  fi
}

# Function to execute command with logging
execute_cmd() {
  local cmd="$1"

  log "EXECUTING: $cmd"
  if [ "$SILENT" = true ]; then
    eval "$cmd" >> "$LOG_FILE" 2>&1
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
      log "ERROR: Command failed with exit code $exit_code"
      return $exit_code
    fi
  else
    eval "$cmd"
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
      log "ERROR: Command failed with exit code $exit_code"
      return $exit_code
    fi
  fi
  return 0
}

# Set up logging
if [ "$SILENT" = true ]; then
  > "$LOG_FILE"  # Clear log file
  log "Running in silent mode. Output logged to $LOG_FILE"
else
  > "$LOG_FILE"  # Clear log file
  log "Running in verbose mode. Output displayed and logged to $LOG_FILE"
fi

# Function to check file and move it safely
download_and_check() {
    local url="$1"
    local temp_file="$2"
    local dest_file="$3"

    log "Downloading from $url to $temp_file..."

    # Download to temporary file
    if ! execute_cmd "wget -q \"$url\" -O \"$temp_file\""; then
        log "ERROR: Failed to download $url"
        return 1
    fi

    # Check file exists
    if ! execute_cmd "[ -f \"$temp_file\" ]"; then
        log "ERROR: Downloaded file $temp_file does not exist"
        return 1
    fi

    # Check file size is greater than 0
    if ! execute_cmd "[ -s \"$temp_file\" ]"; then
        log "ERROR: Downloaded file $temp_file is empty"
        execute_cmd "rm -f \"$temp_file\""
        return 1
    fi

    # Move file to destination
    log "Moving $temp_file to $dest_file..."
    if ! execute_cmd "sudo mv -f \"$temp_file\" \"$dest_file\""; then
        log "ERROR: Failed to move $temp_file to $dest_file"
        execute_cmd "rm -f \"$temp_file\""
        return 1
    fi

    log "Successfully processed $dest_file"
    return 0
}

# Make sure script exits if a command fails
set -e

# Define temporary and destination files
TEMP_1HOSTS="$SCRIPT_DIR/1hosts-lite.rpz.tmp"
TEMP_OISD="$SCRIPT_DIR/oisd.rpz.tmp"
DEST_DIR="/etc/knot-resolver"

# Download and process 1hosts-lite.rpz
if download_and_check "https://o0.pages.dev/Lite/rpz.txt" "$TEMP_1HOSTS" "$DEST_DIR/1hosts-lite.rpz"; then
    log "1hosts-lite.rpz successfully updated"
else
    log "Failed to update 1hosts-lite.rpz"
    exit 1
fi

# Download and process oisd.rpz
if download_and_check "https://small.oisd.nl/rpz" "$TEMP_OISD" "$DEST_DIR/oisd.rpz"; then
    log "oisd.rpz successfully updated"
else
    log "Failed to update oisd.rpz"
    exit 1
fi

log "All RPZ files updated successfully"
exit 0
