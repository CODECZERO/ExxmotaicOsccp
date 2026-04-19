import os
import re

def convert_html_to_tsx(file_path, out_path, component_name):
    if not os.path.exists(file_path):
        return
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    if '<!-- Content Canvas -->' in html:
        content = html.split('<!-- Content Canvas -->', 1)[1].split('</main>')[0]
    elif '<!-- Canvas -->' in html:
        content = html.split('<!-- Canvas -->', 1)[1].split('</main>')[0]
    elif '<section class="mt-16' in html:
        content = '<section class="mt-16' + html.split('<section class="mt-16', 1)[1].split('</main>')[0]
    else:
        content = html
        
    content = content.replace('class=', 'className=')
    content = re.sub(r'(<img[^>]*?)(?<!/)>', r'\1/>', content)
    content = re.sub(r'(<input[^>]*?)(?<!/)>', r'\1/>', content)
    content = re.sub(r'(<hr[^>]*?)(?<!/)>', r'\1/>', content)
    content = content.replace('style="font-variation-settings: \'FILL\' 1;"', 'style={{ fontVariationSettings: "\'FILL\' 1" }}')
    content = re.sub(r'<!--(.*?)-->', r'{/* \1 */}', content)
    content = content.replace('cx="50%" cy="50%" r="84" stroke-dasharray="527" stroke-dashoffset="140"/>', 'cx="50%" cy="50%" r="84" strokeDasharray="527" strokeDashoffset="140"/>')
    content = content.replace('stroke-dasharray', 'strokeDasharray').replace('stroke-dashoffset', 'strokeDashoffset')

    # Remove the bottom body/html tags if they slipped in
    content = content.replace('</body></html>', '')

    tsx_content = f"""import React from 'react';

export default function {component_name}() {{
  return (
    <>
      {{/*  TopNavBar Shell  */}}
      {{/*  Content Canvas  */}}
      <div className="flex-1 w-full relative">
{content}
      </div>
    </>
  );
}}
"""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write(tsx_content)

convert_html_to_tsx('active_session.html', 'web-client/src/app/sessions/page.tsx', 'ActiveSession')
convert_html_to_tsx('network_summary.html', 'web-client/src/app/dashboard/page.tsx', 'NetworkSummary')
convert_html_to_tsx('site_management.html', 'web-client/src/app/sites/page.tsx', 'SiteManagement')
