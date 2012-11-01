fs = require('fs')
path = require('path')
wrench = require('wrench')
util = require('util')
request = require('request')
$ = require('jquery')
md5 = require('./md5')

Bundler = exports

Bundler._fetchedUrls = {}

# Set default options.
Bundler.defaultOptions= {
  outputDir: null,
  baseRewriteUrl: '',
  bundleDir: 'bundled_assets',
  bundleBaseUrl: null
}

RELATIVE_URL_RE = /^[^(http:\/\/|\/)](.*)/

# Helper functions for predictably unique filenames.
Bundler.uniqueFilename = (url) ->
  filename = url.replace(/.*\//, '')
  filenameParts = filename.split('.')
  urlHash = md5.hex_md5(url)
  filenameParts.splice(filenameParts.length-1, 0, urlHash)
  return filenameParts.join('.')

Bundler.bundle = (src, opts={}) ->
  # Merge defaults with provided options.
  opts = $.extend(Bundler.defaultOptions, opts)

  # If using output dir...
  if opts.outputDir
    # Set writeTo to 'consolidated' if not set.
    opts.writeTo ?= opts.outputDir + '/consolidated.css'
    # Create output dir if it does not exist.
    if not fs.existsSync(opts.outputDir)
      wrench.mkdirSyncRecursive(opts.outputDir)

    # If bundle dir is relative...
    if opts.bundleDir?.match(RELATIVE_URL_RE)
      # If bundleBaseUrl is not set...
      if not opts.bundleBaseUrl?
        # Make bundleBaseUrl match bundleDir
        opts.bundleBaseUrl = opts.bundleDir
      # Make bundleDir be relative to output dir.
      opts.bundleDir = path.join(opts.outputDir, opts.bundleDir)

  # Make the bundle dir.
  wrench.mkdirSyncRecursive(opts.bundleDir)

  # Don't add base path to urls.
  less.addBasePath = false

  # Set handler for urls.
  less.rewritePath = (path) ->
    if ! path.match(RegExp('^' + opts.bundleBaseUrl))
      return Bundler.processUrlForBundling(path, opts)
    else
      return path
    
  # Parse.
  parser = new less.Parser({
    paths: [ opts.bundleBaseUrl ? ''],
    filename: 'consolidated'
    })
  parser.parse src, (err, tree) ->
    if err
      console.error('err: ', err)
    bundledCss = tree.toCSS()
    Bundler.postBundle(bundledCss, opts)

# Process a url for bundling.
Bundler.processUrlForBundling = (url, opts={}) ->
  # Rewrite the url per the rewrite rules.
  url = Bundler.rewriteUrl(url, opts.bundleRewrites ? [])
  # If we should fetch the url (per includes and excludes).
  if Bundler.shouldFetchUrl(
    url,
    {includes: opts.bundleIncludes, excludes: opts.bundleExcludes}
  )
    # If the url has not been fetched, fetch it and write to the
    # the target dir.
    if not Bundler._fetchedUrls[url]
      # Get asset filename.
      # We use a hash code on the url to avoid clobbering files with the same name.
      filename = Bundler.uniqueFilename(url)
      
      # Fetch the url.
      srcStream = getStreamForUrl(url)
      targetPath = opts.bundleDir + '/' + filename
      targetStream = fs.createWriteStream(targetPath)

      onError = ->
        console.error("Unable to bundle asset '%s', error: '%j'", url, arguments)
        if opts.bundleFailOnError?
          process.exit(1)

      srcStream.once 'open', (srcFd) ->
        targetStream.once 'open', (targetfd) ->
          util.pump srcStream, targetStream, (error) ->
            if error
              onError()
            else

      srcStream.once 'error', -> onError('src',url, arguments)
      targetStream.once 'error', -> onError('target', targetPath, arguments)

      assetUrl = opts.bundleBaseUrl + '/' + filename
      Bundler._fetchedUrls[url] = assetUrl

    # Fetch processed url from cache.
    processedUrl = Bundler._fetchedUrls[url]
  else
    processedUrl = url
  return processedUrl

# Determine whether a url should be fetched, as per
# opts.includes and opts.excludes.
# opts.includes takes precendence over excludes.
Bundler.shouldFetchUrl = (url, opts={}) ->
  includes = opts.includes ? []
  excludes = opts.excludes ? []

  for inc in includes
    if url.match(inc)
      return true

  for exc in excludes
    if url.match(exc)
      return false

  return true

# Get readStream for the given url.
getStreamForUrl = (url) ->
  if url.match(/^http:\/\//)
    return request(url)
  else
    return fs.createReadStream(url)

Bundler.postBundle = (bundledCss, opts={}) ->
  # If printing...
  if opts.writeTo
    if opts.writeTo == 'stdout'
      process.stdout.write(bundledCss)
    # Write to file for given filename.
    else if typeof opts.writeTo == 'string'
      fs.writeFileSync(opts.writeTo, bundledCss)
    # Write to stream.
    else if opts.writeTo.write?
      opts.writeTo.write(bundledCss)

# Rewrite a url based on the given rewrite rules.
# Last matching rule will be used.
Bundler.rewriteUrl = (url, rewriteRules) ->
  # Loop through rules in reverse order until a match is found.
  for i in [rewriteRules.length - 1..0] by -1
    rule = rewriteRules[i]
    rewrittenUrl = url.replace(rule[0], rule[1])
    # If rewritten url differs, we have matched and should return.
    if rewrittenUrl != url
      return rewrittenUrl
  return url
