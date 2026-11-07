# Publish the installer separately from the website

The EXE is intentionally excluded from Git. It remains above
GitHub's regular Git file limit. A Git-connected Vercel deployment therefore
does not contain `downloads/LocalDictation-Setup.exe`.

Do not remove the EXE ignore rule or commit the binary to the repository.

## Pending release

Repository: `abbasgabol/Flowscribe-Speech-to-text-AI`
Tag: `v0.4.0`
Title: `Local Dictation 0.4.0 beta`
Notes: `packaging/RELEASE-v0.4.0.md`
Assets:

- `qa/lightweight-release/LocalDictation-Setup.exe`
- `qa/lightweight-release/SHA256SUMS.txt`

Upload the assets to a GitHub Release and publish it before deploying the
website link changes. After publishing, update the website links and copy release.json and SHA256SUMS.txt from qa/lightweight-release into website/dist/downloads. The new links must target:

https://github.com/abbasgabol/Flowscribe-Speech-to-text-AI/releases/download/v0.4.0/LocalDictation-Setup.exe

That URL will not work until the release is published. An uploaded private
draft cannot serve anonymous downloads. Verify the published link redirects
to an asset with the expected size, then deploy the website changes to Vercel.

If GitHub CLI is available and authenticated, the release can be staged with:

```powershell
gh release create v0.4.0 --repo abbasgabol/Flowscribe-Speech-to-text-AI --draft --title 'Local Dictation 0.4.0 beta' --notes-file packaging/RELEASE-v0.4.0.md
gh release upload v0.4.0 qa/lightweight-release/LocalDictation-Setup.exe qa/lightweight-release/SHA256SUMS.txt --repo abbasgabol/Flowscribe-Speech-to-text-AI
```

Inspect the asset sizes and checksum, then publish the draft. Do not overwrite
an existing version's asset without checking which build it contains.
