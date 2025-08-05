import os
import tempfile
import shutil
import subprocess
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from git import Repo

@csrf_exempt
@api_view(['POST'])
def add_project(request):
    try:
        data = request.data
        repo_url = data.get('github') or data.get('repo_url')

        if not repo_url:
            return JsonResponse({"error": "GitHub repo URL is required"}, status=400)

        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp()

        try:
            # Clone the repo
            Repo.clone_from(repo_url, temp_dir)

            # Define report path
            report_path = os.path.join(temp_dir, "gitleaks-report.json")

            # Run Gitleaks binary (NOT Docker)
            gitleaks_cmd = [
                "gitleaks",
                "detect",
                "--source", temp_dir,
                "--report-format", "json",
                "--report-path", report_path
            ]

            result = subprocess.run(gitleaks_cmd, capture_output=True, text=True)

            # Gitleaks returns 1 if leaks found, 0 if none
            if result.returncode not in [0, 1]:
                return JsonResponse({
                    "error": "Gitleaks execution failed",
                    "details": result.stderr or result.stdout
                }, status=500)

            # Read the report
            if os.path.exists(report_path):
                with open(report_path, 'r') as f:
                    try:
                        leaks = json.load(f)
                    except json.JSONDecodeError:
                        leaks = []
            else:
                leaks = []

            return JsonResponse({
                "status": "success",
                "repo": repo_url,
                "leaks_found": len(leaks),
                "leaks": leaks
            }, status=200)

        finally:
            # Cleanup
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"Cleanup error: {e}")

    except Exception as e:
        return JsonResponse({
            "error": "Internal Server Error",
            "details": str(e)
        }, status=500)
