# Home Assistant Dashboard

## Prerequisites

Install the following cards via HACS:
- [flex-table-card](https://github.com/custom-cards/flex-table-card)
- [auto-entities](https://github.com/iantrich/config-template-card)
- [button-card](https://github.com/custom-cards/button-card)
- [state-switch](https://github.com/thomasloven/lovelace-state-switch)

## Helper Entity

Create a Dropdown helper in Home Assistant:

**Settings → Devices & Services → Helpers → Create Helper → Dropdown**

| Field | Value |
|---|---|
| Name | `Headscale Filter` |
| Options | `All`, `Online`, `Offline` |

This creates `input_select.headscale_filter`.

## Lovelace Card YAML

Create a new dashboard page at `/lovelace/headscale` and add a Manual card with the following YAML:
```yaml
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: custom:button-card
        name: Online
        icon: mdi:check-network
        show_label: true
        label: |
          [[[
            const all = Object.values(states).filter(s => s.entity_id.startsWith('binary_sensor.headscale_'));
            return all.filter(s => s.state === 'on').length + ' nodes';
          ]]]
        styles:
          card:
            - background: "#1a4a1a"
            - padding: 16px
          name:
            - color: "#4caf50"
            - font-size: 14px
          icon:
            - color: "#4caf50"
          label:
            - color: "#4caf50"
            - font-size: 20px
            - font-weight: bold
      - type: custom:button-card
        name: Offline
        icon: mdi:close-network
        show_label: true
        label: |
          [[[
            const all = Object.values(states).filter(s => s.entity_id.startsWith('binary_sensor.headscale_'));
            return all.filter(s => s.state === 'off').length + ' nodes';
          ]]]
        styles:
          card:
            - background: "#3a1a1a"
            - padding: 16px
          name:
            - color: "#f44336"
            - font-size: 14px
          icon:
            - color: "#f44336"
          label:
            - color: "#f44336"
            - font-size: 20px
            - font-weight: bold
      - type: custom:button-card
        name: Total
        icon: mdi:server-network
        show_label: true
        label: |
          [[[
            const all = Object.values(states).filter(s => s.entity_id.startsWith('binary_sensor.headscale_'));
            return all.length + ' nodes';
          ]]]
        styles:
          card:
            - padding: 16px
          name:
            - font-size: 14px
          icon:
            - color: var(--primary-color)
          label:
            - font-size: 20px
            - font-weight: bold
  - type: horizontal-stack
    cards:
      - type: custom:button-card
        name: All
        icon: mdi:server-network
        entity: input_select.headscale_filter
        tap_action:
          action: call-service
          service: input_select.select_option
          service_data:
            entity_id: input_select.headscale_filter
            option: All
        state:
          - value: All
            styles:
              card:
                - background: var(--primary-color)
              name:
                - color: white
      - type: custom:button-card
        name: Online
        icon: mdi:check-network
        entity: input_select.headscale_filter
        tap_action:
          action: call-service
          service: input_select.select_option
          service_data:
            entity_id: input_select.headscale_filter
            option: Online
        state:
          - value: Online
            styles:
              card:
                - background: "#4caf50"
              name:
                - color: white
      - type: custom:button-card
        name: Offline
        icon: mdi:close-network
        entity: input_select.headscale_filter
        tap_action:
          action: call-service
          service: input_select.select_option
          service_data:
            entity_id: input_select.headscale_filter
            option: Offline
        state:
          - value: Offline
            styles:
              card:
                - background: "#f44336"
              name:
                - color: white
  - type: custom:state-switch
    entity: input_select.headscale_filter
    states:
      All:
        type: custom:auto-entities
        card:
          type: custom:flex-table-card
          title: false
          clickable: true
          sort_by: name
          columns:
            - name: "  "
              prop: state
              modify: "x == 'on' ? '🟢' : '🔴'"
            - name: Node
              attr: friendly_name
              modify: "x.replace('Headscale Nodes ', '')"
            - name: User
              attr: user
            - name: Last Seen
              attr: last_seen_ago
          css:
            table+: "width: 100%; border-collapse: collapse; table-layout: fixed;"
            thead tr th+: "font-size: 11px; text-transform: uppercase; color: var(--secondary-text-color); padding: 6px 4px; white-space: nowrap; overflow: hidden;"
            tbody tr td+: "font-size: 12px; padding: 6px 4px; overflow: hidden; text-overflow: ellipsis;"
            "tbody tr:nth-child(odd)": "background: var(--secondary-background-color);"
            "tbody tr td:nth-child(1)": "width: 8%; text-align: center;"
            "tbody tr td:nth-child(2)": "width: 25%; white-space: normal; word-break: break-word;"
            "tbody tr td:nth-child(3)": "width: 37%; white-space: normal; word-break: break-word;"
            "tbody tr td:nth-child(4)": "width: 30%; white-space: normal;"
        filter:
          include:
            - entity_id: /binary_sensor.headscale_*/
          exclude: []
        sort:
          method: friendly_name
      Online:
        type: custom:auto-entities
        card:
          type: custom:flex-table-card
          title: false
          clickable: true
          sort_by: name
          columns:
            - name: "  "
              prop: state
              modify: "x == 'on' ? '🟢' : '🔴'"
            - name: Node
              attr: friendly_name
              modify: "x.replace('Headscale Nodes ', '')"
            - name: User
              attr: user
            - name: Last Seen
              attr: last_seen_ago
          css:
            table+: "width: 100%; border-collapse: collapse; table-layout: fixed;"
            thead tr th+: "font-size: 11px; text-transform: uppercase; color: var(--secondary-text-color); padding: 6px 4px; white-space: nowrap; overflow: hidden;"
            tbody tr td+: "font-size: 12px; padding: 6px 4px; overflow: hidden; text-overflow: ellipsis;"
            "tbody tr:nth-child(odd)": "background: var(--secondary-background-color);"
            "tbody tr td:nth-child(1)": "width: 8%; text-align: center;"
            "tbody tr td:nth-child(2)": "width: 25%; white-space: normal; word-break: break-word;"
            "tbody tr td:nth-child(3)": "width: 37%; white-space: normal; word-break: break-word;"
            "tbody tr td:nth-child(4)": "width: 30%; white-space: normal;"
        filter:
          include:
            - entity_id: /binary_sensor.headscale_*/
              state: "on"
          exclude: []
        sort:
          method: friendly_name
      Offline:
        type: custom:auto-entities
        card:
          type: custom:flex-table-card
          title: false
          clickable: true
          sort_by: name
          columns:
            - name: "  "
              prop: state
              modify: "x == 'on' ? '🟢' : '🔴'"
            - name: Node
              attr: friendly_name
              modify: "x.replace('Headscale Nodes ', '')"
            - name: User
              attr: user
            - name: Last Seen
              attr: last_seen_ago
          css:
            table+: "width: 100%; border-collapse: collapse; table-layout: fixed;"
            thead tr th+: "font-size: 11px; text-transform: uppercase; color: var(--secondary-text-color); padding: 6px 4px; white-space: nowrap; overflow: hidden;"
            tbody tr td+: "font-size: 12px; padding: 6px 4px; overflow: hidden; text-overflow: ellipsis;"
            "tbody tr:nth-child(odd)": "background: var(--secondary-background-color);"
            "tbody tr td:nth-child(1)": "width: 8%; text-align: center;"
            "tbody tr td:nth-child(2)": "width: 25%; white-space: normal; word-break: break-word;"
            "tbody tr td:nth-child(3)": "width: 37%; white-space: normal; word-break: break-word;"
            "tbody tr td:nth-child(4)": "width: 30%; white-space: normal;"
        filter:
          include:
            - entity_id: /binary_sensor.headscale_*/
              state: "off"
          exclude: []
        sort:
          method: friendly_name
```
