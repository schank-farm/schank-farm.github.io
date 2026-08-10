---
title: "{{ if eq .File.ContentBaseName `index` }}{{ .File.Dir | replaceRE `/` `` | replaceRE `^[0-9]{4}-[0-9]{2}-[0-9]{2}-` `` | replaceRE `-` ` ` | title }}{{ else }}{{ .File.ContentBaseName | replaceRE `^[0-9]{4}-[0-9]{2}-[0-9]{2}-` `` | replaceRE `-` ` ` | title }}{{ end }}"
slug: "{{ if eq .File.ContentBaseName `index` }}{{ .File.Dir | replaceRE `/` `` | replaceRE `^[0-9]{4}-[0-9]{2}-[0-9]{2}-` `` | urlize }}{{ else }}{{ .File.ContentBaseName | replaceRE `^[0-9]{4}-[0-9]{2}-[0-9]{2}-` `` | urlize }}{{ end }}"
date: {{ .Date }}
draft: true
categories: []
description: ""
featured_image: ""
---
