"""
HTTP Upload Service for Playwright MCP Server

This service handles uploading Playwright artifacts and downloads to company API endpoints.
It automatically detects Playwright artifacts folders and uploads files with
proper error handling and cleanup.

Features:
- Auto-detection of Playwright artifacts folders
- Intelligent file filtering (skips non-uploadable files)
- HTTP upload with configurable API endpoint and token
- Local file cleanup after successful upload
- Comprehensive error handling and logging
- Support for both bulk and single file uploads
"""

import glob
import os
from datetime import datetime
from typing import Optional

import requests
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

UNLEASHX_URL = os.getenv("UNLEASHX_URL")


def is_uploadable_file(file_path: str) -> bool:
    """
    Check if a file can be uploaded to the API

    Args:
        file_path (str): Path to the file to check

    Returns:
        bool: True if file can be uploaded, False otherwise
    """
    logger.debug(f"Checking if file is uploadable: {file_path}")
    
    try:
        # Check if it's a regular file (not socket, pipe, etc.)
        if not os.path.isfile(file_path):
            logger.debug(f"  ❌ Not a regular file: {file_path}")
            return False

        # Check file size (skip empty files)
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.debug(f"  ❌ File is empty (0 bytes): {file_path}")
            return False

        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            logger.debug(f"  ❌ File not readable: {file_path}")
            return False

        # Skip certain file types that shouldn't be uploaded
        filename = os.path.basename(file_path).lower()
        skip_extensions = {".lock", ".sock", ".pid", ".tmp", ".log"}
        skip_patterns = {"mysql.sock", "mysqlx.sock", ".lock"}

        # Check file extension
        if any(filename.endswith(ext) for ext in skip_extensions):
            logger.debug(f"  ❌ File has skipped extension: {filename}")
            return False

        # Check filename patterns
        if any(pattern in filename for pattern in skip_patterns):
            logger.debug(f"  ❌ File matches skip pattern: {filename}")
            return False

        logger.debug(f"  ✅ File is uploadable: {file_path} (size: {file_size} bytes)")
        return True

    except Exception as e:
        logger.warning(f"Error checking file {file_path}: {e}")
        logger.warning(f"Error type: {type(e)}")
        return False


def find_playwright_artifacts():
    """
    Find the dynamic Playwright artifacts folder and any download files

    Returns:
        tuple: (folder_path, list_of_files) or (None, []) if not found
    """
    logger.info("=== SEARCHING FOR PLAYWRIGHT ARTIFACTS ===")
    
    # Common Playwright artifacts locations
    artifacts_patterns = [
        "/private/tmp/playwright-artifacts-*",
        "/private/tmp/playwright-*",
        "/tmp/playwright-artifacts-*",
        "/tmp/playwright-*",
        "/tmp/artifacts/playwright_*",
        "/tmp/artifacts/playwright_artifacts_*",
    ]

    logger.info(f"Checking {len(artifacts_patterns)} possible artifact patterns...")
    
    for i, pattern in enumerate(artifacts_patterns, 1):
        logger.info(f"Pattern {i}/{len(artifacts_patterns)}: {pattern}")
        folders = glob.glob(pattern)
        logger.info(f"  Found {len(folders)} folders matching pattern")
        
        for j, folder in enumerate(folders):
            logger.info(f"  Checking folder {j+1}/{len(folders)}: {folder}")
            
            if os.path.isdir(folder):
                logger.info(f"    Folder exists and is a directory")
                # Check if it has uploadable files
                try:
                    files = []
                    folder_contents = os.listdir(folder)
                    logger.info(f"    Folder contains {len(folder_contents)} items")
                    
                    for f in folder_contents:
                        file_path = os.path.join(folder, f)
                        logger.debug(f"      Checking item: {f}")
                        
                        if is_uploadable_file(file_path):
                            files.append(f)
                            logger.info(f"      ✅ Found uploadable file: {f}")
                        else:
                            logger.debug(f"      ❌ Item not uploadable: {f}")

                    if files:
                        logger.info(f"    ✅ Found {len(files)} uploadable files in folder")
                        logger.info(f"    Uploadable files: {files}")
                        logger.info(f"=== PLAYWRIGHT ARTIFACTS FOUND ===")
                        return folder, files
                    else:
                        logger.info(f"    ⚠️ No uploadable files found in this folder")
                        
                except PermissionError:
                    logger.warning(f"    ❌ Permission denied accessing folder: {folder}")
                    continue
                except Exception as e:
                    logger.warning(f"    ❌ Error accessing folder {folder}: {e}")
                    continue
            else:
                logger.debug(f"    Not a directory or doesn't exist")

    logger.info("=== NO PLAYWRIGHT ARTIFACTS FOUND ===")
    logger.info("This is normal if no Playwright operations have been performed yet")
    return None, []


def upload_downloads_to_api(
    downloads_path: Optional[str] = None,
    api_token: Optional[str] = None,
    api_url: str = f"{UNLEASHX_URL}/api/agent-scope/upload-file",
):
    """
    Upload all files from a downloads directory to company API

    Args:
        downloads_path (str, optional): Path to downloads directory. If None, auto-detects.
        api_token (str, optional): API token for authentication. If None, uses environment variable.
        api_url (str): API endpoint URL for file uploads.

    Returns:
        dict: Upload results and status
    """
    start_time = datetime.now()
    logger.info("=== HTTP UPLOAD SERVICE STARTED ===")
    logger.info(f"Function called with downloads_path: {downloads_path}")
    logger.info(f"Function called with api_token: {'Set' if api_token else 'Not set'}")
    logger.info(f"Function called with api_url: {api_url}")
    logger.info(f"Start time: {start_time}")

    try:
        # Get API configuration
        logger.info("Checking API configuration...")
        if not api_token:
            logger.info("No API token provided, checking environment variable...")
            api_token = os.getenv("UNLEASH_AGENT_TOKEN")
            if not api_token:
                logger.error("API token not configured in environment")
                return {
                    "success": False,
                    "error": "API token not configured",
                    "message": "Please set UNLEASH_AGENT_TOKEN environment variable or pass api_token parameter",
                }
            else:
                logger.info("API token found in environment variables")
        else:
            logger.info("API token provided as parameter")

        logger.info(f"Using API URL: {api_url}")
        logger.info(f"UNLEASHX_URL from env: {os.getenv('UNLEASHX_URL')}")

        # Determine downloads path
        logger.info("Determining target downloads path...")
        if downloads_path:
            target_path = downloads_path
            logger.info(f"Using specified downloads path: {target_path}")
        else:
            # Auto-detect Playwright artifacts folder
            logger.info("Auto-detecting Playwright artifacts folder...")
            artifacts_folder, files = find_playwright_artifacts()
            if artifacts_folder and files:
                target_path = artifacts_folder
                logger.info(f"Auto-detected Playwright artifacts folder: {target_path}")
                logger.info(f"Found {len(files)} files in artifacts folder")
            else:
                # Fallback to temp directory
                target_path = "/private/tmp"
                logger.info(f"Using fallback path: {target_path}")
                logger.warning("No Playwright artifacts found, using fallback temp directory")

        # Check if path exists
        logger.info(f"Checking if target path exists: {target_path}")
        if not os.path.exists(target_path):
            logger.error(f"Target path does not exist: {target_path}")
            return {
                "success": False,
                "error": f"Path {target_path} does not exist",
                "message": "Specify a valid downloads path",
            }

        logger.info(f"Target path confirmed: {target_path}")

        # Find uploadable files
        logger.info("Scanning for files in target directory...")
        all_files = [
            f
            for f in os.listdir(target_path)
            if os.path.isfile(os.path.join(target_path, f)) and not f.startswith(".")
        ]
        logger.info(f"Found {len(all_files)} total files in directory")

        # Filter for uploadable files only
        logger.info("Filtering for uploadable files...")
        uploadable_files = [
            f for f in all_files if is_uploadable_file(os.path.join(target_path, f))
        ]
        logger.info(f"Found {len(uploadable_files)} uploadable files")

        if not uploadable_files:
            skipped_count = len(all_files) - len(uploadable_files)
            logger.info(f"No uploadable files found. Total: {len(all_files)}, Skipped: {skipped_count}")
            return {
                "success": True,
                "message": f"No uploadable files found. Found {len(all_files)} total files, {skipped_count} were skipped as non-uploadable.",
                "downloads": [],
                "files_found": len(all_files),
                "files_skipped": skipped_count,
                "files_uploaded": 0,
                "execution_time": "0.00s",
            }

        logger.info(f"Proceeding with {len(uploadable_files)} uploadable files")
        logger.info(f"Uploadable files: {uploadable_files}")

        # Upload files to API
        logger.info("=== STARTING FILE UPLOADS TO API ===")
        results = []
        successful_uploads = 0
        failed_uploads = 0

        for i, filename in enumerate(uploadable_files, 1):
            file_path = os.path.join(target_path, filename)
            logger.info(f"Processing file {i}/{len(uploadable_files)}: {filename}")
            logger.info(f"Full file path: {file_path}")

            try:
                # Upload to API
                logger.info(f"Uploading {filename} to API endpoint: {api_url}")
                logger.info(f"Using headers: {{'token': '***'}}")  # Don't log the actual token

                with open(file_path, "rb") as file:
                    files = {"file": (filename, file, "application/octet-stream")}
                    headers = {"token": api_token}

                    logger.info(f"Sending POST request to API...")
                    response = requests.post(api_url, headers=headers, files=files)
                    logger.info(f"API response received - Status: {response.status_code}")

                    if response.status_code == 200:
                        logger.info(f"✅ API upload successful for {filename}")
                        
                        # Clean up local file after successful upload
                        logger.info(f"Cleaning up local file: {file_path}")
                        os.remove(file_path)
                        logger.info(f"✅ Local file cleaned up successfully")

                        # Parse response if possible
                        try:
                            api_response_data = response.json() if response.text else "Upload successful"
                            logger.info(f"API response data: {api_response_data}")
                        except Exception as parse_error:
                            logger.warning(f"Could not parse API response as JSON: {parse_error}")
                            api_response_data = response.text if response.text else "Upload successful"

                        results.append(
                            {
                                "filename": filename,
                                "api_response": api_response_data,
                                "status": "uploaded_and_cleaned",
                            }
                        )
                        successful_uploads += 1
                        logger.info(f"✅ File {filename} processed successfully (uploaded and cleaned)")
                    else:
                        logger.error(f"❌ API returned status {response.status_code} for {filename}")
                        logger.error(f"Response text: {response.text}")
                        logger.error(f"Response headers: {dict(response.headers)}")
                        
                        results.append(
                            {
                                "filename": filename,
                                "error": f"API status {response.status_code}: {response.text}",
                                "status": "upload_failed",
                            }
                        )
                        failed_uploads += 1

            except Exception as e:
                logger.error(f"❌ Failed to upload {filename}: {e}")
                logger.error(f"Error type: {type(e)}")
                import traceback
                logger.error(f"Full traceback for {filename}: {traceback.format_exc()}")
                
                results.append(
                    {"filename": filename, "error": str(e), "status": "upload_failed"}
                )
                failed_uploads += 1

        elapsed = datetime.now() - start_time
        logger.info(f"=== UPLOAD PROCESS COMPLETED ===")
        logger.info(f"Total execution time: {elapsed.total_seconds():.2f} seconds")
        logger.info(f"Files processed: {len(uploadable_files)}")
        logger.info(f"Successful uploads: {successful_uploads}")
        logger.info(f"Failed uploads: {failed_uploads}")

        # Determine overall success
        overall_success = failed_uploads == 0

        # Create appropriate message
        if successful_uploads > 0 and failed_uploads == 0:
            message = f"Successfully uploaded {successful_uploads} files to API"
            logger.info(f"🎉 {message}")
        elif successful_uploads > 0 and failed_uploads > 0:
            message = f"Partially successful: {successful_uploads} files uploaded, {failed_uploads} failed"
            logger.warning(f"⚠️ {message}")
        else:
            message = f"All {failed_uploads} uploads failed"
            logger.error(f"❌ {message}")

        final_result = {
            "success": overall_success,
            "message": message,
            "downloads": results,
            "files_found": len(all_files),
            "files_skipped": len(all_files) - len(uploadable_files),
            "files_uploaded": successful_uploads,
            "files_failed": failed_uploads,
            "execution_time": f"{elapsed.total_seconds():.2f}s",
        }
        
        logger.info(f"Final result: {final_result}")
        logger.info("=== HTTP UPLOAD SERVICE COMPLETED ===")
        
        return final_result

    except Exception as e:
        elapsed = datetime.now() - start_time
        logger.error(f"=== HTTP UPLOAD SERVICE FAILED ===")
        logger.error(f"Error occurred after {elapsed.total_seconds():.2f} seconds")
        logger.error(f"Error message: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        error_result = {
            "success": False,
            "error": str(e),
            "message": "HTTP upload service failed",
            "execution_time": f"{elapsed.total_seconds():.2f}s",
            "error_type": str(type(e).__name__),
            "error_details": str(e)
        }
        
        logger.error(f"Returning error result: {error_result}")
        logger.error("=== HTTP UPLOAD SERVICE FAILED ===")
        
        return error_result


def upload_specific_file_to_api(
    file_path: str,
    api_token: Optional[str] = None,
    api_url: str = f"{UNLEASHX_URL}/api/agent-scope/upload-file",
):
    """
    Upload a specific file to company API

    Args:
        file_path (str): Path to the file to upload
        api_token (str, optional): API token for authentication. If None, uses environment variable.
        api_url (str): API endpoint URL for file uploads.

    Returns:
        dict: Upload result and status
    """
    start_time = datetime.now()
    logger.info(f"Uploading specific file to API: {file_path}")

    try:
        # Check if file is uploadable
        if not is_uploadable_file(file_path):
            return {
                "success": False,
                "error": f"File {file_path} is not uploadable",
                "message": "File must be a regular, readable file with content",
            }

        # Load environment variables
        load_dotenv()

        # Get API configuration
        if not api_token:
            api_token = os.getenv("UNLEASH_AGENT_TOKEN")
            if not api_token:
                return {
                    "success": False,
                    "error": "API token not configured",
                    "message": "Please set UNLEASH_AGENT_TOKEN environment variable or pass api_token parameter",
                }

        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File {file_path} does not exist",
                "message": "Specify a valid file path",
            }

        # Upload to API
        logger.info(f"Uploading {file_path} to API...")

        with open(file_path, "rb") as file:
            filename = os.path.basename(file_path)
            files = {"file": (filename, file, "application/octet-stream")}
            headers = {"token": api_token}

            response = requests.post(api_url, headers=headers, files=files)

            if response.status_code == 200:
                elapsed = datetime.now() - start_time
                logger.info(
                    f"File uploaded to API successfully in {elapsed.total_seconds():.2f}s"
                )

                return {
                    "success": True,
                    "message": "File uploaded successfully",
                    "api_response": response.json()
                    if response.text
                    else "Upload successful",
                    "execution_time": f"{elapsed.total_seconds():.2f}s",
                }
            else:
                elapsed = datetime.now() - start_time
                logger.error(
                    f"API returned status {response.status_code}: {response.text}"
                )
                return {
                    "success": False,
                    "error": f"API status {response.status_code}: {response.text}",
                    "message": "API upload failed",
                    "execution_time": f"{elapsed.total_seconds():.2f}s",
                }

    except Exception as e:
        elapsed = datetime.now() - start_time
        logger.error(f"HTTP upload failed after {elapsed.total_seconds():.2f}s: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "HTTP upload failed",
            "execution_time": f"{elapsed.total_seconds():.2f}s",
        }


def execute_http_upload_flag():
    """
    Execute HTTP upload when flag is enabled - replicates old check_s3_upload_flag logic
    """
    try:
        logger.info("HTTP Upload Flag Detected!")
        logger.info("Starting HTTP upload operations...")
        
        # Call the main upload function (same as old code)
        result = upload_downloads_to_api()
        logger.info(f"HTTP upload result: {result}")
        
        if result.get("success"):
            files_uploaded = result.get('files_uploaded', 0)
            logger.info(f"Successfully uploaded {files_uploaded} files to API")
            if files_uploaded > 0:
                logger.info(f"Upload details: {result}")
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"HTTP upload failed: {error_msg}")
            logger.error(f"Full error details: {result}")
            
        return result
        
    except Exception as e:
        logger.error(f"HTTP Upload Flag Check Error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Test the service
    logger.info("=== TESTING HTTP UPLOAD SERVICE ===")
    
    # Check environment first
    logger.info("Checking environment configuration...")
    unleashx_url = os.getenv("UNLEASHX_URL")
    agent_token = os.getenv("UNLEASH_AGENT_TOKEN")
    
    logger.info(f"UNLEASHX_URL: {unleashx_url}")
    logger.info(f"UNLEASH_AGENT_TOKEN: {'Set' if agent_token else 'Not set'}")
    
    if not unleashx_url or not agent_token:
        logger.error("Environment not properly configured. Please check your .env file.")
        logger.error("Required variables: UNLEASHX_URL, UNLEASH_AGENT_TOKEN")
        exit(1)

    # Test 1: Upload downloads folder
    logger.info("\n1. Testing upload_downloads_to_api...")
    try:
        result1 = upload_downloads_to_api()
        logger.info(f"Result: {result1}")
    except Exception as e:
        logger.error(f"Test 1 failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Upload specific file
    logger.info("\n2. Testing upload_specific_file_to_api...")
    try:
        test_file = "/tmp/test_upload.txt"
        with open(test_file, "w") as f:
            f.write("Test content for API upload")
            f.write(f"\nCreated at: {datetime.now()}")
        
        logger.info(f"Created test file: {test_file}")
        result2 = upload_specific_file_to_api(test_file)
        logger.info(f"Result: {result2}")
        
        # Cleanup test file
        if os.path.exists(test_file):
            os.remove(test_file)
            logger.info(f"Cleaned up test file: {test_file}")
            
    except Exception as e:
        logger.error(f"Test 2 failed: {e}")
        import traceback
        traceback.print_exc()

    logger.info("\n=== HTTP UPLOAD SERVICE TESTING COMPLETED ===")