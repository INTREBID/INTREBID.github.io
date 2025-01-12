---
layout: page
permalink: /awards/
title: Awards
lang: en
description: Awards and Honors
nav: true
nav_order: 8
---

<!-- 奖项列表 -->
<div class="awards">
  {% assign awards = site.data.awards %}
  {% for award in awards %}
    <div class="award-item">
      <div class="row">
        <div class="col-sm-2">
          {% if award.image %}
            <img src="{{ award.image | relative_url }}" alt="{{ award.title[site.active_lang] }}" class="award-image img-fluid">
          {% else %}
            <img src="/assets/img/blank.png" alt="" class="award-image img-fluid">
          {% endif %}
        </div>
        <div class="col-sm-10">
          {% if award.link %}
            <h3 class="award-title"><a href="{{ award.link }}">{{ award.title[site.active_lang] }}</a></h3>
          {% else %}
            <h3 class="award-title">{{ award.title[site.active_lang] }}</h3>
          {% endif %}
          <p class="award-date">{{ award.date }}</p>
          {% if award.description[site.active_lang] %}
            <p class="award-description">{{ award.description[site.active_lang] }}</p>
          {% endif %}
        </div>
      </div>
    </div>
  {% endfor %}
</div>
