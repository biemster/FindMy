#!/usr/bin/python

import objc; from Foundation import NSBundle, NSClassFromString

AOSKitBundle = NSBundle.bundleWithPath_('/System/Library/PrivateFrameworks/AOSKit.framework')
objc.loadBundleFunctions(AOSKitBundle, globals(), [("retrieveOTPHeadersForDSID", '')])
util = NSClassFromString('AOSUtilities')

print(util.retrieveOTPHeadersForDSID_("-2"))
