{% if installed %}

<div align="center">
  <br><img src="./custom_components/rlp_wetter/icon.png" alt="Icon" width="128"><br><br>
</div>

{% endif%}

{% if not installed %}

<div id="toc">
  <ul align="center" style="list-style: none">
    <summary>
      <h1 style="border-bottom: 0; display: inline-block;">
        <b>🌦️• Rheinland-Pfalz Wetter</b></br>
          <sub><i><u>Home Assistant Integration</i> 🏡</u></sub></h1>
    </summary>
  </ul>
</div>

{% endif%}

<div align="center">

# [API](https://github.com/Bitte-ein-Git/ha_rlp_wetter) used

</div>
</br>

{% if not installed %}
## Installation (Easy)
[![ADD][hacs2]](https://ha-link.heyfordy.de/redirect/hacs_repository/?owner=Bitte-ein-Git&repository=ha_rlp_wetter&category=integration)
## Installation (Manual)
1. Add this Repository to HACS:
   - HACS > 3 dots > "Add custom repository"
   - URL: `Bitte-ein-Git/ha_rlp_wetter`
   - Type: Integration

2. Select "**🌦️ Rheinland-Pfalz Wetterdaten**".

<hr>

> After installation you **have to restart Home Assistant**

{% endif %}

{% if installed and not configured %}

## Configuration

### Easy Configuration (Link to Config Screen)
[![ADD][setup2]](https://ha-link.heyfordy.de/redirect/config_flow_start/?domain=kodi_helpers)
### Manual Configuration
1. Add a new config entry via UI:
   - Go to your Home Assistant **Settings**
   - Select "**Devices & services**"
   - At the bottom right select "**+ Add integration**"

2. Select "**🌦️ Rheinland-Pfalz Wetterdaten**".

{% endif %}

<hr>

[![HACS][hacsbadge]](https://hacs.xyz)