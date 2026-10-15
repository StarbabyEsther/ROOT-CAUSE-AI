# lets one Python program run another program or command.
import subprocess

# runs our pytest command automatically.
result = subprocess.run(
    # collects the test results instead of immediately displaying them.
    ["python", "-m", "pytest", "-v"],
    capture_output=True,
    # makes the captured output readable
    text=True
)

print("Test Results:")
# pytest output
print(result.stdout)
 # contains any error messages written to the error stream
print(result.stderr)

# Check whether the tests passed or failed
if result.returncode == 0:
    print("All tests passed!")

else:
    print("BUG DETECTED!")
    print("Some tests failed.")

# Save the test results to a bug report
if result.returncode == 1:
    with open("bug_report.txt", "w", encoding="utf-8") as file:
        file.write("ROOTCAUSE AI - BUG REPORT\n")
        file.write("=========================\n\n")
        file.write(result.stdout)
        file.write(result.stderr)

    print("Bug report saved successfully!")

